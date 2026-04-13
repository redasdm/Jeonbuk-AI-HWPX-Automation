import { GoogleGenerativeAI } from "@google/generative-ai";

export async function generateWithGemini(apiKey, prompt, systemPrompt) {
  const genAI = new GoogleGenerativeAI(apiKey);
  let result;
  
  try {
    const model = genAI.getGenerativeModel({
      model: "gemini-2.0-flash",
      systemInstruction: systemPrompt,
      generationConfig: {
        temperature: 0.1,
        responseMimeType: "application/json"
      }
    });
    result = await model.generateContent(prompt);
  } catch (e) {
    if (e.message && e.message.includes("503")) {
      console.warn("gemini-2.0-flash high demand (503). Falling back to gemini-1.5-flash...");
      const fallbackModel = genAI.getGenerativeModel({
        model: "gemini-1.5-flash",
        systemInstruction: systemPrompt,
        generationConfig: {
           temperature: 0.1,
           responseMimeType: "application/json"
        }
      });
      result = await fallbackModel.generateContent(prompt);
    } else {
      throw e;
    }
  }

  return result.response.text();
}
