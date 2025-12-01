'use strict';
import React, {useState, useEffect, useRef} from "react";
import {sendMessage, clearChatHistory} from "./api";
import {getChatTaskUrl, getChatUrl} from "./urls";


const ChatMessages = function(props) {
  let thinkingElement = '';
  if (props.hasPendingMessage) {
    const thinkingMessage = {
      content: <p className="add-loading-dots">Thinking</p>,
      message_type: "AI",
      menuUrls: props.menuUrls,
    }
    thinkingElement = <ChatMessage {...thinkingMessage} />
  }
  return (
    <div id="message-list" className="pg-chat-pane">
      {
        props.messages.map((message, index) => {
          return <ChatMessage key={message.id || index} index={index} menuUrls={props.menuUrls} {...message} />;
        })
      }
      {thinkingElement}
    </div>
  );
};

const ChatMessage = function(props) {
  if (props.message_type === "HUMAN") {
    return <HumanMessage {...props} />
  } else {
    return <AIMessage {...props} />
  }
}

const HumanMessage = function(props) {
  const renderAttachment = () => {
    if (!props.attachment_url) return null;
    
    if (props.attachment_type === 'image') {
      return (
        <div className="pg-message-attachment" style={{marginTop: '10px'}}>
          <img src={props.attachment_url} alt="Attachment" style={{maxWidth: '300px', maxHeight: '300px', borderRadius: '8px'}} />
        </div>
      );
    } else {
      return (
        <div className="pg-message-attachment" style={{marginTop: '10px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px'}}>
          <a href={props.attachment_url} target="_blank" rel="noopener noreferrer">
            📎 {props.attachment_type?.toUpperCase()} file: {props.attachment_url.split('/').pop()}
          </a>
        </div>
      );
    }
  };
  
  return (
    <div className="pg-chat-message-user">
      <div className="pg-chat-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5"
             stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round"
                d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
        </svg>
      </div>
      <div className="pg-message-contents">
        {props.content && <div>{props.content}</div>}
        {renderAttachment()}
      </div>
    </div>
  );
};

const MenuOptions = function(props) {
  if (!props.menuUrls) return null;
  
  const menuStyle = {
    marginTop: '15px',
    padding: '12px',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
    border: '1px solid #e9ecef',
  };
  
  const sectionStyle = {
    marginBottom: '12px',
  };
  
  const sectionTitleStyle = {
    fontWeight: '600',
    fontSize: '14px',
    marginBottom: '6px',
    color: '#495057',
  };
  
  const linkStyle = {
    display: 'block',
    padding: '4px 8px',
    color: '#007bff',
    textDecoration: 'none',
    fontSize: '13px',
    borderRadius: '4px',
  };
  
  const linkHoverStyle = {
    backgroundColor: '#e7f3ff',
  };
  
  return (
    <div style={menuStyle}>
      <div style={sectionStyle}>
        <div style={sectionTitleStyle}>Solutions</div>
        <a href={props.menuUrls.solutions.budgeting} style={linkStyle} target="_blank" rel="noopener noreferrer">Budgeting</a>
        <a href={props.menuUrls.solutions.debt_consolidation} style={linkStyle} target="_blank" rel="noopener noreferrer">Debt Consolidation</a>
        <a href={props.menuUrls.solutions.investment_savings} style={linkStyle} target="_blank" rel="noopener noreferrer">Investment & Savings</a>
        <a href={props.menuUrls.solutions.tax_optimization} style={linkStyle} target="_blank" rel="noopener noreferrer">Tax Optimization</a>
        <a href={props.menuUrls.solutions.credit_improvement} style={linkStyle} target="_blank" rel="noopener noreferrer">Credit Improvement</a>
      </div>
      <div style={sectionStyle}>
        <div style={sectionTitleStyle}>Records</div>
        <a href={props.menuUrls.records.insights} style={linkStyle} target="_blank" rel="noopener noreferrer">Portfolio Insights</a>
        <a href={props.menuUrls.records.explorer} style={linkStyle} target="_blank" rel="noopener noreferrer">Records Explorer</a>
        <a href={props.menuUrls.records.upload} style={linkStyle} target="_blank" rel="noopener noreferrer">Upload Records</a>
        <a href={props.menuUrls.records.link_account} style={linkStyle} target="_blank" rel="noopener noreferrer">Online Financial Accounts</a>
        {props.menuUrls.records.personal_sensitive && (
          <a href={props.menuUrls.records.personal_sensitive} style={linkStyle} target="_blank" rel="noopener noreferrer">Personal Sensitive Information</a>
        )}
      </div>
      <div style={sectionStyle}>
        <div style={sectionTitleStyle}>Account</div>
        <a href={props.menuUrls.account.subscription} style={linkStyle} target="_blank" rel="noopener noreferrer">Subscription</a>
        <a href={props.menuUrls.account.profile} style={linkStyle} target="_blank" rel="noopener noreferrer">Profile</a>
        <a href={props.menuUrls.account.change_password} style={linkStyle} target="_blank" rel="noopener noreferrer">Change Password</a>
        <a href={props.menuUrls.account.logout} style={linkStyle} target="_blank" rel="noopener noreferrer">Sign out</a>
      </div>
    </div>
  );
};

const AIMessage = function(props) {
  return (
    <div className="pg-chat-message-system">
      <div className="pg-chat-icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
             strokeLinecap="round" strokeLinejoin="round">
          <path
            d="M7 7h10a2 2 0 0 1 2 2v1l1 1v3l-1 1v3a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2v-3l-1 -1v-3l1 -1v-1a2 2 0 0 1 2 -2z"></path>
          <path d="M10 16h4"></path>
          <circle cx="8.5" cy="11.5" r=".5" fill="currentColor"></circle>
          <circle cx="15.5" cy="11.5" r=".5" fill="currentColor"></circle>
          <path d="M9 7l-1 -4"></path>
          <path d="M15 7l1 -4"></path>
        </svg>
      </div>
      <div className="pg-message-contents">
        {props.content}
        {props.menuUrls && <MenuOptions menuUrls={props.menuUrls} />}
      </div>
    </div>
  );
};

const InputBar = function(props) {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }
  
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      const fileType = file.type.toLowerCase();
      const fileName = file.name.toLowerCase();
      const isImage = fileType.startsWith('image/') || fileName.match(/\.(jpg|jpeg|png|gif|webp)$/);
      const isCSV = fileType === 'text/csv' || fileName.endsWith('.csv');
      const isPDF = fileType === 'application/pdf' || fileName.endsWith('.pdf');
      
      if (isImage || isCSV || isPDF) {
        setSelectedFile(file);
      } else {
        alert('Please select an image, CSV, or PDF file.');
        event.target.value = '';
      }
    }
  }
  
  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }
  
  const handleSend = () => {
    if (props.message.trim() || selectedFile) {
      props.sendMessage(props.message, selectedFile);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }
  
  return (
    <div className="pg-chat-input-bar">
      {selectedFile && (
        <div style={{padding: '8px', marginBottom: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
          <span>📎 {selectedFile.name}</span>
          <button type="button" onClick={handleRemoveFile} style={{background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px'}}>×</button>
        </div>
      )}
      <div style={{display: 'flex', gap: '8px', alignItems: 'center', width: '100%'}}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept="image/*,.csv,.pdf"
          style={{display: 'none'}}
          id="file-input"
        />
        <label htmlFor="file-input" style={{cursor: 'pointer', padding: '8px', border: '1px solid #ddd', borderRadius: '4px'}}>
          📎
        </label>
        <input
          name="message"
          type="text"
          placeholder="Type your message..."
          aria-label="Message"
          className="pg-control"
          value={props.message}
          onChange={(event) => props.setMessage(event.target.value)}
          onKeyPress={handleKeyPress}
          style={{flex: 1}}
        />
        <button type="submit" className="pg-button-primary" onClick={handleSend}>
          Send
        </button>
      </div>
    </div>
  );
}

function getWelcomeMessage(menuUrls) {
  return {
    key: -1,
    message_type: "AI",
    content: "Hello, what can I help you with today?",
    menuUrls: menuUrls,
  };
}


function getErrorMessage(menuUrls) {
  return {
    message_type: "AI",
    content: <p className="pg-text-danger">
      Sorry something went wrong. This may be an OpenAI error, or your API key may not be set properly.
      If you are a site administrator seeing this for the first time, double check your <code>OPENAI_API_KEY</code>
      setting / environment variable and restart all running processes.
    </p>,
    menuUrls: menuUrls,
  };
}

const ChatApplication = function(props) {
  const [messages, setMessages] = useState([getWelcomeMessage(props.menuUrls), ...props.chat.messages.map(msg => ({...msg, menuUrls: props.menuUrls}))]);
  const [inputMessage, setInputMessage] = useState("");
  const [currentTaskId, setCurrentTaskId] = useState(null);

  useEffect(() => {
    // scroll to bottom on new messages
    const chatUI = document.getElementById('message-list');
    if (chatUI) {
      chatUI.scrollTop = chatUI.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (currentTaskId) {
      const taskUrl = getChatTaskUrl(props.apiUrls['chat:api_get_message_response'], props.chat.id, currentTaskId);
      const fetchData = async () => {
        try {
          const response = await fetch(taskUrl);
          const jsonResponse = await response.json();
          if (jsonResponse.complete) {
            if (jsonResponse.success) {
              addMessage({...jsonResponse.result, menuUrls: props.menuUrls});
            } else {
              addMessage(getErrorMessage(props.menuUrls))
            }
            setCurrentTaskId(null);
          } else {
            window.setTimeout(fetchData, 1000);
          }
        } catch (error) {
          console.error('Fetch error:', error);
        }
      };
      fetchData();
    }
  }, [currentTaskId])

  const addMessage = (message) => {
    const newMessages = [...messages, message];
    setMessages(newMessages);
  }
  
  const inputChanged = (message) => {
    setInputMessage(message);
  }
  
  const sendMessageCallback = (responseData) => {
    if (responseData.error) {
      alert('Error: ' + responseData.error);
      return;
    }
    setCurrentTaskId(responseData.task_id);
    addMessage({...responseData, menuUrls: props.menuUrls});
    setInputMessage("");
  }
  
  const sendMessageWrapper = (message, attachment) => {
    const apiUrl = getChatUrl(props.apiUrls['chat:api_new_chat_message'], props.chat.id)
    return sendMessage(apiUrl, props.chat.id, message, attachment, sendMessageCallback);
  }
  
  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all chat history?')) {
      const clearUrl = getChatUrl(props.apiUrls['chat:api_clear_chat'], props.chat.id);
      clearChatHistory(clearUrl, (response) => {
        if (response.error) {
          alert('Error: ' + response.error);
        } else {
          setMessages([getWelcomeMessage(props.menuUrls)]);
        }
      });
    }
  }
  
  return  (
    <>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', padding: '10px', borderBottom: '1px solid #ddd'}}>
        <h2 style={{margin: 0}}>AI Chat Assistant</h2>
        <button 
          onClick={handleClearHistory}
          className="pg-button"
          style={{padding: '8px 16px', fontSize: '14px'}}
        >
          Clear History
        </button>
      </div>
      <ChatMessages messages={messages} hasPendingMessage={Boolean(currentTaskId)} menuUrls={props.menuUrls}/>
      <InputBar chat={props.chat} message={inputMessage} setMessage={inputChanged} sendMessage={sendMessageWrapper}/>
    </>
  );
}

export default ChatApplication;
