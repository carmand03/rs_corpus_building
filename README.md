This repository documents an integrated pipeline for building and refining an exhaustive historical newspaper corpus using a combination of LLMs and more conventional NLP methods. It is centered on the topic of returned students in the Chinese (Shenbao) and English-language presses, but we believe the pipeline is adaptable to other research queries.

The repository structure follows the steps of the pipeline (see linked SVG):
	•	Initial query using HistText
	•	Query expansion with embeddings
	•	OCR quality assessment using the Impresso pipeline
	•	Relevance classification using LLMs, with two options: OpenAI API or Ollama (local)
	•	Article segmentation using LLMs, with two options: OpenAI API or Ollama (local
