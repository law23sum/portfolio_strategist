

// note: these must match what's set by the django template.
// see `api_url_helpers.py` for an example
const CHAT_PLACEHOLDER = '__chat_id__';
const TASK_PLACEHOLDER = '__task_id__';


export const getChatUrl = function(urlTemplate, chatId) {
  if (!urlTemplate) return '';
  return urlTemplate.replace(CHAT_PLACEHOLDER, chatId);
};


export const getChatTaskUrl = function(urlTemplate, chatId, taskId) {
  if (!urlTemplate) return '';
  return urlTemplate.replace(CHAT_PLACEHOLDER, chatId).replace(TASK_PLACEHOLDER, taskId);
};
