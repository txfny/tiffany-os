# LinkedIn Post Draft v4

in 2020 i started working out with zero plans. just a goal and a dream. youtube videos in my living room, showing up to the gym and hoping the workouts i found online will work. and it did work eventually but it was slow. i had to overtime learn my form, programming, nutrition all at once and honestly just guessing most of the time.

my dad had been telling me for years that i should train smarter, pay attention to how my body actually works. i didn't listen. then i saw something on tiktok about how women's training should change based on their cycle. that your body literally responds differently to intensity depending on where you are hormonally. and suddenly what my dad had been saying clicked. i looked at every app, every program, every routine i'd been following and realized they're all built around male physiology. none of them accounted for this.

when chatgpt came out in 2022 i used it mostly for school. but once custom GPTs launched in late 2023 i thought, okay, i could actually build something that accounts for this. i made a fitness coaching agent. three inputs: my weight, my cycle day, and whether i was working out at home or at the gym. it would give me a session that was supposedly tailored to where i was in my cycle.

and it was cool for like three days. then it forgot what i lifted previous week, started giving me the same workout twice, and i'd re-paste everything just for it to work one session and go right back to making stuff up. i even gaslit myself for a while thinking "maybe i'm supposed to repeat this workout." i made separate versions for my sister and my friend so we could keep our data apart. same problem times three. none of them held up.

so i dropped it. went back to asking chatgpt for a template week, getting bored of it, asking for another one. basically back to guessing.

about a year went by. and in that time i was learning things that would eventually change how i thought about this problem. my mentor at dell, [@MENTOR_NAME], was teaching me how models actually work. how they chunk information, how retrieval augmented generation gives a model the right data at the right time instead of hoping it remembers. i was building RAG systems, working with nvidia on scalable AI architecture, publishing papers on it. i took machine learning classes for my masters. then i moved to microsoft and started working with cloud infrastructure every day.

at some point i looked at my old fitness agent and realized the problem was obvious. i had been asking the model to remember things. to hold onto my training history, my cycle day, my weights, my progression, across conversations that expire. that's not what models are good at. what they're good at is reasoning. i just needed to give it the right data to reason over.

so i started building again. this time with claude code, which lets you define exactly how the model should behave through a file called `CLAUDE.md`. i wrote real rules this time. readiness scoring based on biometrics. progression logic. the cycle-aware training i'd been wanting since the beginning. i thought okay, if i just write good enough instructions, the model will follow them.

it didn't.

i'd catch claude saying it couldn't find my session history when the files were literally right there in the repo. one time i had two claude instances open in the same project and they gave me completely different session types for the same day. one said "run and core" for thursday, the other correctly said "strength full body and core." same rules, same files, two different answers.

it doesn't matter how good your instructions are if the model can interpret them differently every time. i was still trusting the model with things the model shouldn't own.

so i started pulling things out of claude's hands. one by one. session type? that's a function now. it reads the weekly template and returns what today is. no interpretation. readiness scoring? a function. i give it my HRV (heart rate variability, basically how recovered your nervous system is), resting heart rate, sleep, energy, and symptoms. it computes a readiness tier and tells claude exactly how much volume and intensity i can handle that day. working weights? fetched from a database so claude can't round up or guess. i built guardrails on both ends. before a session starts, a validator checks if any recent sessions are missing from the log so claude isn't planning around incomplete data. after a session is logged, another validator checks for errors before anything gets saved.

all of this runs on cloud functions. claude calls them, reads the output, and builds around it.

claude owns reasoning. code owns data.

it doesn't drift anymore. it doesn't forget. it doesn't confidently tell me to squat a weight i haven't hit yet. and when i come back weeks later it picks up right where i left off because the truth lives in files and endpoints, not in a conversation that expires.

no app. no dashboard. just me talking to my terminal and it actually knowing what it's talking about. the personalized, cycle-aware, biometrics-driven coaching i wanted back in 2020. it just took five years and a lot of broken prototypes to figure out how to build it right.
