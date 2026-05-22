
list_models:
	@echo Gathering available models...
	@uv run python list_genai_models.py

test:
	@echo Running tests...
	@uv run python -m unittest discover -s langchain_agents/voice_sandwich/tests -p "test*.py" -v

voice-sandwich:
	@concurrently -n "FastAPI,Serve" -c "green,yellow" \
			"uv run python -m langchain_agents.voice_sandwich.back_end.main" \
			"cd langchain_agents/voice_sandwich/front-end && serve . -p 3000"
