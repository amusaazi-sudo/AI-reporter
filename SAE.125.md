## Part 5: Project - AI-Powered Report Generation and Emailing

![responding to a letter](https://intra-content-image-bucket.s3.eu-north-1.amazonaws.com/img/uJWEiN7.png)

Welcome to your second practical project-graded task! 🚀

This project builds upon your previous work with Python fundamentals, loops, conditionals (from the Chess project), and your recent experience with the OpenAI API from the hands-on exercise. The challenge here shifts towards integrating different components: fetching real-world data, processing it using an AI model, and delivering the result in a practical format (email). As with the previous project, you'll also practice writing tests and handling potential errors.

## Project Description

In this practical exercise, you will develop a Python program that fetches information from a public API, uses an AI language model (like GPT-4.1 via OpenRouter) to generate a human-readable summary or report based on that data, and then sends this AI-generated content as an email message.

**Leveraging Your Previous Work:** Remember the hands-on exercise where you built a command-line chatbot using the `openai` library? You'll use the same core concepts here: interacting with the ChatCompletion API (via OpenRouter), managing API keys securely, and handling API responses.

**The requirements you are given to implement are as follows:**

1.  **Command-Line Interface:**
 - The program should accept two command-line arguments: an email address (to send the report to) and a "report type" identifier (e.g., `weather`, `news_summary`, `stock_update` - you define what types your program supports).
 - Example run command: `python ai_reporter.py user@example.com weather`

2.  **Input Validation:**
 - Your program should check if the user has provided the correct number of command-line arguments.
 - The email address provided should be validated (a simple check for "@" and "." is sufficient).
 - The program should check if the `report_type` argument corresponds to one of your implemented types.

3.  **Data Fetching:**
 - Based on the `report_type` argument, your program should call at least one relevant public API to fetch data. (e.g., a weather API if the type is `weather`, a news API if the type is `news_summary`).
 - You need to implement support for at least **two different report types**, each likely using a different public API.
 - A good place to explore free APIs is [this GitHub repo](https://github.com/public-apis/public-apis). Choose APIs that provide data suitable for summarization or reporting by an LLM.

4.  **AI-Powered Content Generation:**
 - Take the raw data fetched from the public API.
 - Process this data using the OpenRouter ChatCompletion API (leveraging the `openai` library with `base_url="https://openrouter.ai/api/v1"` and skills from the previous exercise).
 - **Design a suitable prompt** to instruct the AI model (e.g., `openai/gpt-5-mini`) to generate a concise, human-readable summary, report, or message based on the fetched data. The desired output format should be suitable for an email body.
 - Handle the AI's response. The generated text will be the core content of your email.
 - Manage your OpenRouter API key securely via the `OPENROUTER_API_KEY` environment variable (use your key from Sprint 1).

5.  **Email Sending:**
 - Send the AI-generated content via email to the address provided in the command-line arguments.
 - You should use a Gmail account to send it. (We recommend a throwaway account just in case you accidentally leave your login details in the code). As per the original project, **use Python's in-built `smtplib` library** for this.
 - **Important:** Setting up `smtplib` with Gmail often requires enabling "Less secure app access" or, preferably, generating an "App Password" for your Gmail account. Research Google's current recommendations for sending emails programmatically via `smtplib`. We recommend creating a new Gmail account specifically for this exercise.

6.  **Error Handling & Testing:**
 - Your program must use `try/except` statements at least once to handle potential errors (e.g., API connection issues, invalid API keys, email sending failures).
 - Your program must have at least **three meaningful unit tests** using `pytest`. Consider testing: input validation, mocking API calls (both public API and OpenRouter API), and checking the basic structure of the email preparation.

As before, list any assumptions you make about the requirements if they are not explicitly stated here.

You should research how to interact with your chosen public APIs and troubleshoot the Gmail sending process.

## Reviewer Role

In this project, imagine you are presenting your work to a **fellow AI Engineer** on your team. They understand the basics of Python, APIs, and LLMs but want to see how you've integrated these components. They're interested in:
- How you fetched the external data.
- How did you structure the prompt for the LLM to get the desired output?
- How did you handle potential issues (errors, API limits)?
- The overall code structure and clarity.

Be prepared to explain your design choices, particularly regarding how you have iterated on your prompt, how you handled the data flow from the public API to the LLM and finally into the email.

## Project Evaluation Criteria

- **Command-Line Interface:** Program accepts and correctly parses the email address and report type arguments.
- **Input Validation:** Arguments are checked for validity (format, supported types).
- **Data Fetching:** Program successfully calls at least one relevant public API based on the report type (minimum two report types implemented).
- **LLM Integration:** The Program correctly uses the OpenRouter API (via the OpenAI-compatible SDK) to process the fetched data.
- **Email Sending:** The Program successfully sends the AI-generated content using `smtplib` and Gmail.
- **Unit Tests:** At least three meaningful unit tests are present and pass.
- **Error Handling:** At least one `try/except` block is used effectively.
- **Code Quality:** Code is well-organized, readable, uses meaningful names, and includes comments where necessary. Adherence to basic Python style conventions (e.g., PEP 8).

During a task review, you may get asked questions that test your understanding of covered topics.

**Sample questions for a reviewer to ask (a reviewer is encouraged and expected to think of more, however!)**

- Can you walk me through the data flow, from fetching the raw data to generating the final email content?
- How did you design the prompt for the OpenRouter API? What challenges did you encounter, and how did you iterate on it?
- How are you handling your API keys securely?
- What kind of errors did you anticipate, and how does your `try/except` block handle them?
- What aspects of your chosen public API's response were most important for the LLM prompt?
- Why did you choose these specific unit tests? What edge cases do they cover (or not cover)?
- What are the potential limitations or costs associated with using the OpenRouter API in this project?


## Submission:

Read an [in-depth guide about reviews here](https://doku.turingcollege.com/p/0771306d-bc1e-4b00-9153-c63adeb63a85).

### Submission and Scheduling a Project Review

To submit the project and allow the reviewer to view your work beforehand, you need to use the Github repository that has been created for you.
Please go through these material to learn more about submitting projects, scheduling project reviews and using Github:

- [Completing a Sprint, Submitting a Project and Scheduling Reviews](https://doku-v02-production.up.railway.app/p/f3dbf8bc-2dae-4230-938d-3144110ea74a)
- [Git and GitHub for Beginners](https://www.youtube.com/watch?v=RGOj5yH7evk)


**Estimate average time to complete: 15-20 hours**
