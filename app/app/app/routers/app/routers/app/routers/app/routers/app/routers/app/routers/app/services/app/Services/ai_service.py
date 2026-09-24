import openai
from typing import List, Dict, Optional


class AIService:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    async def chat(self, message: str, context: Optional[str] = None,
                   history: List[Dict[str, str]] = None) -> str:
        system_prompt = """You are RamsTech AI, an expert mechanic and auto electrician assistant.

EXPERTISE:
- Diesel and petrol engines
- Transmissions (manual, automatic, CVT)
- Hydraulic systems
- Pneumatic systems
- Automotive electronics (ECU, sensors, CAN bus)
- Braking, suspension, steering
- All vehicles: cars, bakkies, trucks, buses, tractors, boats, bikes, earth movers

RESPONSE FORMAT:
- Safety warnings in CAPS
- Numbered step-by-step instructions
- Required tools list
- Torque specs
- Estimated time & difficulty
- Common mistakes to avoid

Be practical and workshop-ready."""

        if context:
            system_prompt += f"\n\nCONTEXT: {context}"

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.3,
        )
        return response.choices[0].message.content

    async def diagnose(self, symptoms: str, vehicle: Optional[str] = None,
                       system: Optional[str] = None) -> str:
        prompt = f"""TROUBLESHOOTING REQUEST
Symptoms: {symptoms}
Vehicle: {vehicle or 'Not specified'}
System: {system or 'Not specified'}

Provide:
1. Possible causes (ranked)
2. Diagnostic steps
3. Tests to perform
4. Repair procedure
5. Safety warnings"""
        return await self.chat(prompt)
