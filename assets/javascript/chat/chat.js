'use strict';
import React from "react";
import {createRoot} from "react-dom/client";
import ChatApplication from "./ChatApplication";

const domContainer = document.querySelector('#chat-content');
const chat = JSON.parse(document.getElementById('chat').textContent);
const apiUrls = JSON.parse(document.getElementById('api-urls').textContent);



const root = createRoot(domContainer);
root.render(
  <ChatApplication chat={chat} apiUrls={apiUrls} />
);
