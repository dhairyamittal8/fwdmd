# FwdMD demo video script (about 2:40)

Record with QuickTime (File → New Screen Recording) and the mic on. Before you start, have the live site open, plus the /evaluation page in a second tab.

---

**0:00–0:25 · Hook and personal story** (on camera, or over the home page)
> "Every Indian family has a WhatsApp group, and every one of them gets forwards like this: 'Dengue? Drink hot lemon water, no need to go to hospital.' I grew up in Kolkata and Guwahati watching these spread in my own family. Later I worked at Factifi, a misinformation platform, and learned that the fact-checks exist. They just never reach the uncle who forwarded the message, in his language, in a tone he'll accept."

**0:25–0:45 · The problem** (stay on the home page)
> "India accounted for the largest share of fact-checked COVID misinformation worldwide, nearly 16% of items across 138 countries. India has 530 million WhatsApp users, and research shows users over 65 are the most vulnerable. So I built FwdMD."

**0:45–1:35 · Live demo** (screen)
1. Click **Hinglish: dengue + nimbu paani**, then **Check forward**.
   > "I paste the forward, in Hinglish, exactly as it arrives."
2. While it loads (about 10 seconds):
   > "Claude pulls out the specific medical claims and checks each one only against a curated evidence pack of 42 common Indian health myths from WHO, ICMR, MoHFW and PIB."
3. Point at the red banner:
   > "First, a red flag: this forward tells people with dengue to skip the hospital, and that can kill."
4. Scroll through the verdicts:
   > "Each claim gets a verdict with a real source I can click. If the evidence pack doesn't cover a claim, FwdMD says UNVERIFIED rather than guessing."
5. Scroll to the reply, then click **Share on WhatsApp**:
   > "And here's the part I care most about: a kind reply in the same language that I can send straight back to the family group."

**1:35–2:10 · Evaluation** (switch to the /evaluation tab)
> "Because this is health, I wanted evidence, not vibes. I benchmarked the same model on PUBHEALTH, a public-health fact-checking dataset, using 200 stratified test claims. It hit 81% accuracy and 67.7 macro-F1. That's about 14 points above published zero-shot GPT-4, and close to models fine-tuned on this exact dataset. One honest negative result: my more complex multi-step pipeline didn't beat simple direct labelling, and I report that on the page."

**2:10–2:30 · Safety design** (open How it works)
> "The safety features are designed in from the start. The server drops any citation the model invents, verdicts without a real source become UNVERIFIED, nothing is stored, and there's a permanent 'not medical advice' banner."

**2:30–2:45 · Roadmap and close** (back to the home page)
> "Next: clinician review of the evidence pack, a benchmark built from real Indian-language forwards, and a WhatsApp bot so people can forward messages to FwdMD directly. I'm Dhairya, and this is FwdMD: fact-checks that actually make it back into the family group."

---
**Tips:** one take is fine. If the demo is slow, pause the recording while it loads. Export at 1080p and upload to YouTube as Unlisted, then paste that link into Devpost.
