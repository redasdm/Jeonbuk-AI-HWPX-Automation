import { hasKey, loadKey } from '../settings/key-store.js';
import { SYSTEM_PROMPT, parseResponseBlocks } from './prompt-builder.js';
import { generateWithGemini } from './gemini-client.js';
import { generateWithClaude } from './claude-client.js';
import { generateWithOpenAI } from './openai-client.js';

export async function generateDocument(prompt, modelType) {
  if (!hasKey(modelType)) {
    throw new Error(`API key for ${modelType} is not set.`);
  }

  const apiKey = loadKey(modelType);
  let rawJsonStr = "";

  try {
    if (modelType === 'gemini') {
      rawJsonStr = await generateWithGemini(apiKey, prompt, SYSTEM_PROMPT);
    } else if (modelType === 'claude') {
      rawJsonStr = await generateWithClaude(apiKey, prompt, SYSTEM_PROMPT);
    } else if (modelType === 'openai') {
      rawJsonStr = await generateWithOpenAI(apiKey, prompt, SYSTEM_PROMPT);
    }

    const docModel = JSON.parse(rawJsonStr);
    docModel.blocks = parseResponseBlocks(docModel.blocks, docModel.template);
    return docModel;
  } catch (err) {
    console.error("AI Generation failed", err);
    throw new Error("문서 생성 중 오류가 발생했습니다: " + err.message);
  }
}
