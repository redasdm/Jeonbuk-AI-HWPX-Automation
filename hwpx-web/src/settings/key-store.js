const KEYS = { gemini: "hwpx_gemini_key", claude: "hwpx_claude_key", openai: "hwpx_openai_key" };

export const saveKey = (model, key) => localStorage.setItem(KEYS[model], key);
export const loadKey = (model) => localStorage.getItem(KEYS[model]) || "";
export const deleteKey = (model) => localStorage.removeItem(KEYS[model]);
export const hasKey = (model) => !!loadKey(model);
