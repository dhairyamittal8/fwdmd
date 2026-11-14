"use client";

import { useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import type { CheckResult } from "@/lib/schema";

const EXAMPLES = [
  {
    label: "Hinglish: dengue + nimbu paani",
    text: "Dengue ho gaya? Garam paani mein nimbu daal ke piyo, platelets badh jayenge, hospital jaane ki zaroorat nahi. Papite ke patte ka juice do din mein theek kar deta hai. Sabko forward karo! 🙏",
  },
  {
    label: "हिंदी: कोरोना और गोमूत्र",
    text: "ज़रूरी सूचना: कोरोना से बचने के लिए रोज़ सुबह गोमूत्र पिएं और भाप लें। गर्म पानी पीने से वायरस गले में ही मर जाता है। इसे सभी ग्रुप में भेजें।",
  },
  {
    label: "English: stop BP & diabetes tablets",
    text: "URGENT from a retired doctor: STOP your BP and diabetes tablets! These chemicals destroy your kidneys. Drink karela juice every morning and eat 2 raw garlic cloves - sugar and BP become normal in 7 days. My uncle stopped his insulin and is fully cured. Share with everyone you love!",
  },
];

const VERDICT_STYLE: Record<string, string> = {
  TRUE: "bg-green-600 text-white",
  FALSE: "bg-red-600 text-white",
  MISLEADING: "bg-amber-500 text-black",
  UNVERIFIED: "bg-gray-500 text-white",
};

const MAX_IMAGE_BYTES = 3_500_000;

type Img = { media_type: string; data: string; name: string };

function readImage(file: File): Promise<Img> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => {
      const url = String(r.result);
      resolve({ media_type: file.type, data: url.slice(url.indexOf(",") + 1), name: file.name });
    };
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}

export default function Checker() {
  const [text, setText] = useState("");
  const [image, setImage] = useState<Img | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CheckResult | null>(null);
  const [copied, setCopied] = useState(false);

  async function check(forward: string, img: Img | null) {
    if (!forward.trim() && !img) {
      setError("Paste a forward or add a screenshot first.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    setCopied(false);
    try {
      const res = await fetch("/api/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: forward,
          image: img ? { media_type: img.media_type, data: img.data } : undefined,
        }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok || !data || data.error) {
        setError(data?.error ?? "Something went wrong. Please try again.");
      } else {
        setResult(data as CheckResult);
      }
    } catch {
      setError("Couldn't reach the checker. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!["image/jpeg", "image/png", "image/webp", "image/gif"].includes(file.type)) {
      setError("Please upload a JPG, PNG, WEBP or GIF screenshot.");
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setError("That screenshot is too big (max 3.5 MB). Try cropping it.");
      return;
    }
    setError(null);
    setImage(await readImage(file));
  }

  async function copyReply() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.reply);
      setCopied(true);
    } catch {
      setError("Couldn't copy. Please select the reply and copy it by hand.");
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <p className="text-sm font-medium">Try an example:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <Button
              key={ex.label}
              variant="outline"
              size="sm"
              disabled={loading}
              onClick={() => {
                setText(ex.text);
                setImage(null);
                check(ex.text, null);
              }}
            >
              {ex.label}
            </Button>
          ))}
        </div>
      </div>

      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          check(text, image);
        }}
      >
        <label htmlFor="forward" className="sr-only">
          WhatsApp forward
        </label>
        <Textarea
          id="forward"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste the WhatsApp forward here…"
          rows={6}
          maxLength={6000}
        />
        <div className="flex flex-wrap items-center gap-3">
          <label className={buttonVariants({ variant: "outline", size: "sm" }) + " cursor-pointer"}>
            {image ? "Change screenshot" : "Add screenshot"}
            <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" className="sr-only" onChange={onFile} />
          </label>
          {image && (
            <span className="text-sm text-muted-foreground">
              {image.name}{" "}
              <button type="button" className="underline" onClick={() => setImage(null)}>
                remove
              </button>
            </span>
          )}
          <Button type="submit" disabled={loading} className="ml-auto">
            {loading ? "Checking…" : "Check forward"}
          </Button>
        </div>
      </form>

      {loading && (
        <p role="status" className="animate-pulse text-sm text-muted-foreground">
          Reading the forward and checking each claim against our sources…
        </p>
      )}

      {error && (
        <div role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-900">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {result.red_flag.triggered && (
            <div role="alert" className="rounded-md bg-red-600 p-4 text-white">
              <p className="font-bold">⚠️ Warning: this forward could put someone in danger</p>
              <p className="text-sm">{result.red_flag.reason}</p>
              <p className="mt-1 text-sm">Don&apos;t stop medicine or delay care without talking to a doctor.</p>
            </div>
          )}

          <p className="text-sm text-muted-foreground">Detected language: {result.detected_language}</p>

          {result.claims.map((c, i) => (
            <Card key={i}>
              <CardHeader className="gap-2">
                <Badge className={VERDICT_STYLE[c.verdict]}>{c.verdict}</Badge>
                <CardTitle className="text-base leading-snug">{c.claim}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>{c.explanation}</p>
                {c.sources.length > 0 && (
                  <ul className="space-y-1">
                    {c.sources.map((s) => (
                      <li key={s.id}>
                        <a
                          href={s.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary underline underline-offset-2"
                        >
                          {s.source_org}: {s.source_title}
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          ))}

          <Card className="border-primary">
            <CardHeader>
              <CardTitle className="text-base">Reply you can send back</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="whitespace-pre-wrap rounded-md bg-[#dcf8c6] p-3 text-sm text-black">{result.reply}</p>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" onClick={copyReply}>
                  {copied ? "Copied!" : "Copy"}
                </Button>
                <a
                  href={`https://wa.me/?text=${encodeURIComponent(result.reply)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={buttonVariants({ size: "sm" })}
                >
                  Share on WhatsApp
                </a>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
