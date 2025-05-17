FOR RUNNING THE STREAMLIT APP HEAD TO THIS LINK-- https://reflectionsai-qhgsh7rvpfappdti4az9xk9.streamlit.app/
---

# ReflectionsAI 📖✨  

ReflectionsAI is an innovative journaling application that merges the therapeutic benefits of journaling with the power of artificial intelligence. Designed to provide a seamless and reflective journaling experience, ReflectionsAI empowers users to write, reflect, and gain deeper insights into their personal growth journey.

---

## 🌟 Features  

- **✍️ Write**: A sleek interface to pen down your thoughts and feelings effortlessly.  
- **💭 Reflect**: Retrieve and review your past journal entries stored securely in Snowflake for personal insights.  
- **🤖 Chat**: Interact with an AI assistant to explore your journal in unique ways, ask reflective questions, or seek inspiration.  

---

## 💻 Tech Stack  

- **Frontend**: [Streamlit](https://streamlit.io/) for an interactive and responsive user interface.  
- **Backend**:  
  - **Snowflake**: Handles secure storage and querying of journal entries.  
  - **Snowflake Cortex**: Leverages advanced search capabilities for journal entry retrieval.  
  - **Mistral-large2**: A language model powering natural language interactions.  

---

## 🛠️ Running 

1. Login into snowflake, create necessary tables and datasets, a cortex search service.
---

## 📜 Usage  

1. **Home Page**  
   Get a quick overview of the app's capabilities.  

2. **Write Entry**  
   - Express yourself in the journal entry interface.  
   - Save your entries, which are securely stored in Snowflake.  

3. **Chat with AI**  
   - Interact with the AI assistant for deeper insights into your journal.  
   - Use options like context-based querying and chat history.  

---

## 🧩 Architecture  

1. **Streamlit Frontend**  
   Provides an intuitive interface with custom styling for enhanced user experience.  

2. **Snowflake Integration**  
   - Securely stores journal entries in the `JOURNAL_DB.PUBLIC` schema.  
   - Enables Cortex search services for efficient context retrieval.  

3. **AI Assistant**  
   - Powered by the `mistral-large2` model, offering empathetic and insightful responses.  
   - Utilizes chat history and journal context for enriched interactions.  

---

## 🛡️ Security  

- Data is securely stored in Snowflake.  
- Contextual interactions ensure privacy and relevance.  

---

## 🚀 Future Enhancements  

- Add sentiment analysis to journal entries for emotional insights.  
- Introduce voice-to-text journaling for hands-free entry.  
- Enable cross-device synchronization for a seamless experience.  

---

## 🤝 Contributing  

Contributions are welcome! Please fork the repository, make your changes, and submit a pull request.  

---

## 📄 License  

This project is licensed under the MIT License.  

---

## 🙏 Acknowledgments  

- [Streamlit](https://streamlit.io/)  
- [Snowflake](https://www.snowflake.com/)  
- [Mistral AI](https://mistral.ai/)  

---

Feel free to adapt or modify the README to match your specific needs!
