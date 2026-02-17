// static/js/config.js
export const API_BASE   = 
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
  ? "http://127.0.0.1:8008"
  : "";
export const PROJECT_ID = 1;          // the project you created in Swagger
export const CHAT_ID    = 1;          // your chat id (integer)
export const X_USER_ID  = "veyra-001"; // same header you used in Swagger
