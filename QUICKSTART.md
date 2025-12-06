# Quick Start Guide

Get your Book Learning App running in 5 minutes!

## Step 1: Install Dependencies (2 min)

```bash
cd book-learning-app
uv sync
```

Or if you don't have `uv` installed yet:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Then sync dependencies
uv sync
```

## Step 2: Set Up LLM Studio (2 min)

1. Download and install **LLM Studio** from https://lmstudio.ai/
2. Open LLM Studio
3. Download a model (recommended: **Mistral 7B Instruct** or **Llama 3.1 8B**)
4. Click the **"↔"** icon to start the local server
5. Verify it shows "Server running on port 1234"

## Step 3: Configure Environment (30 sec)

```bash
cp .env.example .env
```

The defaults should work. If LLM Studio runs on a different port, edit `.env`:

```
LLM_STUDIO_URL=http://localhost:YOUR_PORT/v1
```

## Step 4: Test Setup (30 sec)

```bash
uv run test_setup.py
```

Should show all tests passing ✓

## Step 5: Run the App (10 sec)

```bash
uv run app.py
```

Open your browser to: **http://localhost:5000**

## Step 6: Upload Your First Book

1. Click **"Choose a book (PDF or EPUB)"**
2. Select a PDF or EPUB file
3. Click **"Upload and Process"**
4. Wait 1-5 minutes (grab coffee ☕)
5. Explore your personalized learning plan!

## Example Workflow

Once your book is processed:

1. **View Learning Plan** - See 8-15 key topics extracted
2. **Study Topic 1** - Chat with AI tutor about the first concept
3. **Ask Questions** - "Can you explain this with an example?"
4. **Generate Exercises** - Click button to create practice problems
5. **Complete Exercises** - Test your understanding
6. **Move to Next Topic** - Mark complete and continue

## Troubleshooting

### LLM Studio not connecting?

```bash
# Test manually
curl http://localhost:1234/v1/models
```

Should return model information. If not:
- Make sure LLM Studio server is running (green indicator)
- Check the port number matches
- Restart LLM Studio

### Book upload fails?

- Try a smaller PDF first (< 100 pages)
- Make sure PDF is not password-protected
- Check file is valid (can you open it?)

### Processing is slow?

- Normal! Large books take 3-5 minutes
- First topic extraction pass analyzes full book
- Subsequent topics are faster
- Use smaller books for testing

## Tips

- **Best models for learning:** Mistral 7B Instruct, Llama 3.1 8B
- **Start small:** Try a short book or single chapter first
- **Interactive learning:** Ask follow-up questions in chat
- **Practice:** Always generate exercises to reinforce learning
- **Experiment:** Try different books on different subjects

## What to Try

Good books to start with:
- Programming tutorials (clear concepts)
- Academic textbooks (structured content)
- Non-fiction guides (well-organized)
- Technical documentation (specific topics)

## Next Steps

1. Upload a book
2. Study the first topic
3. Generate exercises
4. Read the full [SETUP.md](SETUP.md) for advanced features
5. Customize prompts in `src/llm_client.py`

## Need Help?

Check the console output - it shows detailed progress:
```
Processing book: mybook.pdf
Parsing book: mybook.pdf
Analyzing 'My Book' to extract learning topics...
Extracted 12 topics from 'My Book'
Extracting context for topic 1/12: Introduction
```

If something fails, you'll see specific error messages there.

---

**Ready to learn? Start uploading books and have AI-powered conversations about any topic!**
