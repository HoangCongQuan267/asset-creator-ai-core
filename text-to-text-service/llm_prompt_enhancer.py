import torch
from transformers import pipeline


class LLMPromptEnhancer:
    # ------------------------------------------------------------------
    # STRICT CONSTRAINTS (The "Secret Sauce" for Quality)
    # ------------------------------------------------------------------
    # These phrases MUST appear in the final prompts to guarantee SDXL quality.
    REQUIRED_POSITIVE = "masterpiece, best quality, 8k, ultra-detailed"
    REQUIRED_NEGATIVE = (
        "low quality, worst quality, bad anatomy, bad hands, text, error, "
        "missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, "
        "signature, watermark, username, artist name"
    )

    def __init__(self, model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        """
        Initialize the LLM-based prompt enhancer using a lightweight local model.
        Args:
            model_id (str): HuggingFace model ID. Defaults to TinyLlama (1.1B parameters) for speed.
        """
        print(f"Loading LLM model: {model_id}...")

        # Determine device
        self.device = (
            "mps"
            if torch.backends.mps.is_available()
            else "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )
        print(f"Running LLM on: {self.device}")

        # Load pipeline
        # We use torch_dtype=torch.float16 for efficiency on GPU/MPS
        dtype = torch.float16 if self.device != "cpu" else torch.float32

        self.pipe = pipeline(
            "text-generation",
            model=model_id,
            torch_dtype=dtype,
            device_map="auto"
            if self.device != "cpu"
            else None,  # auto handles mps/cuda often, but explicit device might be safer for pipeline if auto fails
        )
        print("LLM loaded successfully.")

    def enhance_prompt(self, user_idea, style="cinematic"):
        """
        Uses the LLM to generate a detailed positive and negative prompt based on the user's idea.
        """

        # Construct the instruction for the LLM
        # TinyLlama Chat format:
        # <|system|>
        # {system_message}
        # </s>
        # <|user|>
        # {user_message}
        # </s>
        # <|assistant|>

        system_prompt = (
            "You are an expert AI art prompt engineer for Stable Diffusion XL. "
            "Your goal is to format the user's idea into a professional prompt WITHOUT adding unrequested content.\n"
            "RULES for Positive Prompt:\n"
            "- DO NOT hallucinate new objects, actions, or narrative details not mentioned by the user.\n"
            "- Structure: [User's Exact Idea] -> [Art Style/Medium] -> [Lighting/Atmosphere] -> [Quality Boosters].\n"
            f"- Always include: '{self.REQUIRED_POSITIVE}'.\n"
            "RULES for Negative Prompt (CRITICAL for avoiding errors):\n"
            f"- ALWAYS include: '{self.REQUIRED_NEGATIVE}'.\n"
            "- If the subject is human, add: 'deformed, disfigured, mutation, extra limbs, floating limbs'.\n"
            "Strictly follow this output format:\n"
            "Positive Prompt: <generated_positive_prompt>\n"
            "Negative Prompt: <generated_negative_prompt>\n"
            "\n"
            "Example:\n"
            "Positive Prompt: A samurai, ukiyo-e style, dramatic lighting, masterpiece, best quality, 8k, ultra-detailed\n"
            "Negative Prompt: low quality, worst quality, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, signature, watermark, username, artist name"
        )

        user_message = f"Convert this idea into a professional prompt pair.\nIdea: {user_idea}\nStyle: {style}"

        prompt_template = f"<|system|>\n{system_prompt}</s>\n<|user|>\n{user_message}</s>\n<|assistant|>\n"

        # Generate
        outputs = self.pipe(
            prompt_template,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            num_return_sequences=1,
            pad_token_id=self.pipe.tokenizer.eos_token_id,
        )

        generated_text = outputs[0]["generated_text"]

        # Extract the assistant's response (remove the prompt part)
        response = generated_text.split("<|assistant|>\n")[-1].strip()

        return self._parse_response(response)

    def _parse_response(self, response_text):
        """
        Parses the raw text response into a dictionary AND enforces constraints.
        """
        positive = ""
        negative = ""

        lines = response_text.split("\n")
        current_section = None

        for line in lines:
            clean_line = line.strip()
            if clean_line.lower().startswith("positive prompt:"):
                current_section = "positive"
                positive += clean_line.split(":", 1)[1].strip() + " "
            elif clean_line.lower().startswith("negative prompt:"):
                current_section = "negative"
                negative += clean_line.split(":", 1)[1].strip() + " "
            elif current_section == "positive":
                positive += clean_line + " "
            elif current_section == "negative":
                negative += clean_line + " "

        # Clean up strings
        positive = positive.strip()
        negative = negative.strip()

        # Fallback if parsing fails (LLM hallucination or format break)
        if not positive:
            positive = response_text

        # ---------------------------------------------------------
        # PROGRAMMATIC ENFORCEMENT
        # (Guarantee the constraints are present, even if LLM forgot)
        # ---------------------------------------------------------

        # Enforce Positive Constraints
        if self.REQUIRED_POSITIVE not in positive:
            positive = f"{positive}, {self.REQUIRED_POSITIVE}"

        # Enforce Negative Constraints
        if self.REQUIRED_NEGATIVE not in negative:
            # Check if it's empty, we don't want ", low quality..." at start if empty
            if negative:
                negative = f"{negative}, {self.REQUIRED_NEGATIVE}"
            else:
                negative = self.REQUIRED_NEGATIVE

        return {"positive": positive, "negative": negative}


if __name__ == "__main__":
    # Test block
    enhancer = LLMPromptEnhancer()

    while True:
        idea = input("\nEnter your idea (or 'q' to quit): ")
        if idea.lower() == "q":
            break
        style = input("Enter style (e.g., cyberpunk, fantasy, realistic): ")

        print("\nGenerating...")
        result = enhancer.enhance_prompt(idea, style)

        print("\n--- Result ---")
        print(f"Positive: {result['positive']}")
        print(f"Negative: {result['negative']}")
        print("--------------")
