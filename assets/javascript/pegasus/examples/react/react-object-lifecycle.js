'use strict';
import React from "react";
import {createRoot} from "react-dom/client";
import EmployeeApplication from "./App";
import {getPegasusApiClient} from "../../pegasus";
import {BrowserRouter} from "react-router-dom";


const domContainer = document.querySelector('#object-lifecycle-home');
const root = createRoot(domContainer);
root.render(
  <BrowserRouter basename={urlBase}>
    <EmployeeApplication client={getPegasusApiClient(SERVER_URL_BASE)} urlBase="/" emptyImage={STATIC_FILES.undraw_empty}/>
  </BrowserRouter>
);
