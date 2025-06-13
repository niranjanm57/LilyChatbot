import React, { useState, useEffect } from "react";
import "./Chatbot.css";
import { motion } from "framer-motion";

const Chatbot = () => {
  const [messages, setMessages] = useState([
    { text: "Hello! I am Lily, your cooking assistant! 🍳", sender: "bot" }
  ]);
  const [input, setInput] = useState("");
  const [audio, setAudio] = useState(null);

  useEffect(() => {
    if (audio) {
      audio.play();
    }
  }, [audio]);

  const extractDishName = (text) => {
    const commonPhrases = ["recipe for", "make", "prepare", "cook", "Hey Lily"];
    let cleanedText = text.toLowerCase();
    commonPhrases.forEach((phrase) => {
      cleanedText = cleanedText.replace(phrase, "").trim();
    });
    return cleanedText.charAt(0).toUpperCase() + cleanedText.slice(1);
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { text: input, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);

    const dishName = extractDishName(input);
    const isIngredients = input.includes(",") || input.toLowerCase().includes("i have");

    try {
      if (isIngredients) {
        const response = await fetch(`http://127.0.0.1:5000/search-by-ingredients?ingredients=${encodeURIComponent(input)}`);
        const data = await response.json();

        if (data.suggestions && data.suggestions.length > 0) {
          const botMessage = {
            text: (
              <>
                <strong>Based on your ingredients, try these recipes:</strong>
                <ul className="recipe-list">
                  {data.suggestions.map((title, index) => (
                    <li key={index}>{title}</li>
                  ))}
                </ul>
              </>
            ),
            sender: "bot"
          };
          setMessages((prev) => [...prev, botMessage]);
        } else {
          setMessages((prev) => [...prev, { text: "Couldn't find recipes with those ingredients. Try others!", sender: "bot" }]);
        }
      } else {
        const response = await fetch(`http://127.0.0.1:5000/get-recipe?name=${encodeURIComponent(dishName)}`);
        const data = await response.json();

        if (data.recipe) {
          const botMessage = {
            text: (
              <>
                <strong>Here is the recipe for {data.recipe.title}:</strong>
                <ul className="recipe-list">
                  {data.recipe.ingredients.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
                <div className="recipe-steps">
                  {data.recipe.steps.map((step, index) => (
                    <p key={index} className="recipe-step">Step {index + 1}: {step}</p>
                  ))}
                </div>
              </>
            ),
            sender: "bot"
          };
          setMessages((prev) => [...prev, botMessage]);
          if (data.voice) {
            setAudio(new Audio(`http://127.0.0.1:5000${data.voice}`));
          }
        } else {
          setMessages((prev) => [...prev, { text: "Sorry, I couldn't find that recipe. Please try again.", sender: "bot" }]);
        }
      }
    } catch (error) {
      setMessages((prev) => [...prev, { text: "Error processing request.", sender: "bot" }]);
    }

    setInput("");
  };

  const handleVoiceInput = () => {
    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
    };
  };

  return (
    <div className="chat-background-wrapper">
      <video autoPlay loop muted className="bg-video">
        <source src="/bg1.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>
  
      <div className="chat-wrapper">
  <div className="chat-card">
    <div className="chat-header">Lily Chef Bot 🍽️</div>
    <div className="chat-container">
          <div className="chat-box">
            {messages.map((msg, index) => (
              <motion.div
                key={index}
                className={msg.sender === 'bot' ? 'bot-message' : 'user-message'}
                initial={{ opacity: 0, x: msg.sender === 'bot' ? -50 : 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
              >
                {msg.text}
              </motion.div>
            ))}
          </div>
          <div className="chat-input">
            <input
              type="text"
              placeholder="Ask me a recipe or say what ingredients you have..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            <button onClick={handleSendMessage}>➤</button>
            <button className="mic-button" onClick={handleVoiceInput}>🎤</button>
          </div>
        </div>
      </div>
      </div></div>
  );
  
};

export default Chatbot;
