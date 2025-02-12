import {Cookies} from "../app";
import {getChatUrl} from "./urls";


export const sendMessage = (apiUrl, chat_id, message, callBack) => {
  const messageData = {
    chat: chat_id,
    message_type: "HUMAN",
    content: message,
  }
  fetch(apiUrl, {
    method: "POST",
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': Cookies.get('csrftoken'),
    },
    body: JSON.stringify(messageData),
  }).then((response) => {
    if (response.ok) {
      return response.json();
    }
  }).then((data) => {
    callBack(data);
  });
}
