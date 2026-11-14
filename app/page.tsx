import Checker from "@/components/checker";

export default function Home() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Got a health forward?</h1>
        <p className="text-muted-foreground">
          Paste it (English, Hindi, Bengali or Hinglish) or add a screenshot. We check it against WHO, ICMR, MoHFW and
          PIB sources and write a kind reply you can send back.
        </p>
      </div>
      <Checker />
    </div>
  );
}
