import {Cookies} from "../app";
import {getChatUrl} from "./urls";


export const sendMessage = (apiUrl, chat_id, message, attachment, callBack) => {
  const formData = new FormData();
  formData.append('chat', chat_id);
  formData.append('message_type', 'HUMAN');
  formData.append('content', message || '');
  
  if (attachment) {
    formData.append('attachment', attachment);
  }
  
  fetch(apiUrl, {
    method: "POST",
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': Cookies.get('csrftoken'),
    },
    body: formData,
  }).then((response) => {
    if (response.ok) {
      return response.json();
    }
    throw new Error('Failed to send message');
  }).then((data) => {
    callBack(data);
  }).catch((error) => {
    console.error('Error sending message:', error);
    callBack({ error: error.message });
  });
}

export const clearChatHistory = (apiUrl, callBack) => {
  fetch(apiUrl, {
    method: "POST",
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': Cookies.get('csrftoken'),
    },
  }).then((response) => {
    if (response.ok) {
      return response.json();
    }
    throw new Error('Failed to clear chat history');
  }).then((data) => {
    callBack(data);
  }).catch((error) => {
    console.error('Error clearing chat history:', error);
    callBack({ error: error.message });
  });
}
