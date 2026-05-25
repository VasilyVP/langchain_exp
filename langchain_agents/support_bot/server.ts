import { config as dotenv } from 'dotenv';
import { REST, Routes, Client, GatewayIntentBits, ChannelType, TextChannel } from 'discord.js';
import { createAgent, SystemMessage, HumanMessage } from "langchain";
import { MemorySaver } from "@langchain/langgraph";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";


dotenv();

if (!process.env.DISCORD_BOT_TOKEN || !process.env.DISCORD_APPLICATION_ID) {
  console.error('Error: DISCORD_BOT_TOKEN or DISCORD_APPLICATION_ID is not defined in the environment variables.');
  process.exit(1);
}

// Register slash commands
const commands = [
  {
    name: 'support',
    description: 'Open support thread'
  }
];

const rest = new REST()
  .setToken(process.env.DISCORD_BOT_TOKEN);

await rest.put(
  Routes.applicationCommands(process.env.DISCORD_APPLICATION_ID),
  { body: commands }
);

// listening for interactions
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

client.once('clientReady', () => {
  console.log(`Logged in as ${client.user?.tag}`);
});
client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === 'support') {
    // Private threads are only available in regular guild text channels.
    const channel = interaction.channel;
    if (channel?.type === ChannelType.GuildText) {
      const thread = await channel.threads.create({
        name: `support -> ${interaction.user.username}`,
        autoArchiveDuration: 1440, // 24 hours
        type: ChannelType.PrivateThread,
        invitable: true,
      });
      await thread.members.add(interaction.user.id);
      await thread.send(`Hello ${interaction.user}, welcome to your support thread!\nDescribe your issue and our support team will assist you shortly.`);
      //await thread.send('Please note that this thread will be archived after 24 hours of inactivity.');
    } else {
      await interaction.reply({
        content: 'Private support threads can only be opened in a regular server text channel.',
        ephemeral: true
      });
      return;
    }


    await interaction.reply('Support thread opened!');

    // Here you can add logic to create a support thread or channel
  }
});

const systemPrompt = new SystemMessage(`
  You are a helpful and friendly customer support assistant.
  You assist users with their queries and provide accurate information.
  Always be polite and professional in your responses.
`);

const model = new ChatGoogleGenerativeAI({
  model: 'gemma-4-31b-it',
  apiKey: process.env.GOOGLE_API_KEY,
});

const agent = createAgent({
  model,
  systemPrompt,
  checkpointer: new MemorySaver(),
});

// listen for messages
client.on('messageCreate', async (message) => {
  try {
    const parentChannelId = (message.channel as TextChannel)?.parentId;
    if (message.author.bot) return;
    if (parentChannelId !== process.env.DISCORD_CHANNEL_ID) return;
    if (message.channelId == process.env.DISCORD_CHANNEL_ID) return;

    console.log('Message received:', message.content);

    await message.channel.sendTyping();

    const response = await agent.invoke(
      { messages: [new HumanMessage(message.content)] },
      { configurable: { thread_id: message.channelId } },
    );

    const responseText = response.messages.at(-1)?.text ?? 'Sorry, I could not generate a response.';
    
    console.log('Generated response:', responseText);

    await message.reply(responseText);
  } catch (error) {
    console.error('Error processing message:', error);
    await message.reply('Sorry, something went wrong while processing your request.');
  }
});

client.login(process.env.DISCORD_BOT_TOKEN);
