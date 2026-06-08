import { useEffect, useRef, useState } from "react";
import {
  Box, Heading, Input, Button, HStack, Text, Progress, Alert, AlertIcon,
} from "@chakra-ui/react";
import { api, type Job } from "../api";

const STAGE_PCT: Record<string, number> = {
  queued: 8, crawling: 30, extracting: 65, scoring: 90, done: 100, error: 100,
};
const STAGE_LABEL: Record<string, string> = {
  queued: "Queued…",
  crawling: "Crawling the website…",
  extracting: "Extracting business intelligence…",
  scoring: "Calculating ABI score…",
  done: "Done",
  error: "Failed",
};

export function RunPanel({ onComplete }: { onComplete: (domain: string) => void }) {
  const [url, setUrl] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => () => { if (timer.current) window.clearInterval(timer.current); }, []);

  const start = async () => {
    setErr(null);
    if (!url.trim()) return;
    try {
      const j = await api.startRun(url.trim());
      setJob(j);
      if (timer.current) window.clearInterval(timer.current);
      timer.current = window.setInterval(async () => {
        const cur = await api.run(j.run_id);
        setJob(cur);
        if (cur.status === "done" || cur.status === "error") {
          if (timer.current) window.clearInterval(timer.current);
          if (cur.status === "done" && cur.domain_ready) onComplete(cur.domain);
        }
      }, 1500);
    } catch (e) {
      setErr(String(e));
    }
  };

  const running = job?.status === "running" || job?.status === "queued";

  return (
    <Box bg="white" borderWidth="1px" borderColor="gray.200" rounded="xl" p={5} shadow="sm">
      <Heading size="sm" mb={2}>
        Score a website
      </Heading>
      <HStack>
        <Input
          placeholder="example-hvac.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !running && start()}
          isDisabled={running}
        />
        <Button colorScheme="blue" onClick={start} isLoading={running} loadingText="Running" px={6}>
          Run
        </Button>
      </HStack>

      {job && job.status !== "error" && (
        <Box mt={4}>
          <Text fontSize="sm" color="gray.600" mb={1}>
            {STAGE_LABEL[job.stage] ?? job.stage}{" "}
            <Text as="span" color="gray.400">
              ({job.domain})
            </Text>
          </Text>
          <Progress
            value={STAGE_PCT[job.stage] ?? 10}
            size="sm"
            rounded="full"
            colorScheme="blue"
            isAnimated
            hasStripe={running}
          />
        </Box>
      )}

      {job?.status === "error" && (
        <Alert status="error" mt={4} rounded="md" fontSize="sm">
          <AlertIcon />
          {job.error || "Run failed"}
        </Alert>
      )}
      {err && (
        <Alert status="error" mt={4} rounded="md" fontSize="sm">
          <AlertIcon />
          {err}
        </Alert>
      )}
    </Box>
  );
}
