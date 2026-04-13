import OpenAI from "openai";

export async function generateWithOpenAI(apiKey, prompt, systemPrompt) {
  const client = new OpenAI({ apiKey, dangerouslyAllowBrowser: true });
  
  const response = await client.chat.completions.create({
    model: "gpt-4o",
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: prompt }
    ],
    temperature: 0.2,
    response_format: { type: "json_object" }
  });

  return response.choices[0].message.content;
}
