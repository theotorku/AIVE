import { Box, Heading, Flex, Text, Badge, VStack, Input } from "@chakra-ui/react";
import { useMemo, useState } from "react";
import { GRADE_COLOR, type SiteSummary } from "../api";

export function SitesGallery({
  sites,
  selected,
  onSelect,
}: {
  sites: SiteSummary[];
  selected: string | null;
  onSelect: (domain: string) => void;
}) {
  const [q, setQ] = useState("");
  const filtered = useMemo(
    () =>
      sites.filter(
        (s) =>
          s.domain.toLowerCase().includes(q.toLowerCase()) ||
          (s.business_name || "").toLowerCase().includes(q.toLowerCase())
      ),
    [sites, q]
  );

  return (
    <Box bg="white" borderWidth="1px" borderColor="gray.200" rounded="xl" p={4} shadow="sm">
      <Heading size="sm" mb={2}>
        Scored sites <Text as="span" color="gray.400">({sites.length})</Text>
      </Heading>
      <Input size="sm" placeholder="Filter…" mb={3} value={q} onChange={(e) => setQ(e.target.value)} />
      <VStack align="stretch" spacing={1} maxH="60vh" overflowY="auto">
        {filtered.map((s) => (
          <Flex
            key={s.domain}
            justify="space-between"
            align="center"
            px={3}
            py={2}
            rounded="md"
            cursor="pointer"
            bg={selected === s.domain ? "blue.50" : "transparent"}
            _hover={{ bg: "gray.100" }}
            onClick={() => onSelect(s.domain)}
          >
            <Box minW={0}>
              <Text fontSize="sm" fontWeight="medium" noOfLines={1}>
                {s.business_name || s.domain}
              </Text>
              <Text fontSize="xs" color="gray.500" noOfLines={1}>
                {s.domain}
              </Text>
            </Box>
            <Badge bg={GRADE_COLOR[s.grade ?? ""] ?? "gray.400"} color="white" minW="44px" textAlign="center">
              {s.overall ?? "—"} {s.grade}
            </Badge>
          </Flex>
        ))}
      </VStack>
    </Box>
  );
}
