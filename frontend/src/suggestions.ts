export const curatedDisciplines = [
  "Agricultural Sciences",
  "Anthropology",
  "Architecture",
  "Artificial Intelligence",
  "Bioinformatics",
  "Biology",
  "Biomedical Engineering",
  "Business",
  "Chemistry",
  "Climate Science",
  "Computer Science",
  "Data Science",
  "Earth Sciences",
  "Economics",
  "Education",
  "Engineering",
  "Environmental Science",
  "Epidemiology",
  "European Studies",
  "Law",
  "Linguistics",
  "Materials Science",
  "Mathematics",
  "Medicine",
  "Neuroscience",
  "Physics",
  "Political Science",
  "Psychology",
  "Public Health",
  "Robotics",
  "Social Sciences",
  "Sociology",
  "Statistics",
  "Sustainability",
];

export const curatedKeywords = [
  "AI ethics",
  "bioinformatics",
  "cancer research",
  "climate adaptation",
  "clinical AI",
  "computational biology",
  "cybersecurity",
  "data visualization",
  "digital health",
  "energy systems",
  "genomics",
  "green transition",
  "health equity",
  "human-computer interaction",
  "machine learning",
  "medical imaging",
  "migration studies",
  "natural language processing",
  "public policy",
  "quantum technologies",
  "remote sensing",
  "renewable energy",
  "science communication",
  "social innovation",
  "urban resilience",
];

const blockedSuggestionTerms = [
  "agency",
  "bureau",
  "center",
  "centre",
  "commission",
  "department",
  "foundation",
  "institute",
  "mission",
  "ministry",
  "national",
  "office",
  "program",
  "programme",
  "u.s.",
  "usaid",
];

export function cleanSuggestion(value: string): string | null {
  const suggestion = value.trim().replace(/\s+/g, " ");
  const lower = suggestion.toLowerCase();
  if (suggestion.length < 3 || suggestion.length > 48) return null;
  if (/https?:|www\.|@/.test(lower)) return null;
  if (/[.;:()[\]{}]/.test(suggestion)) return null;
  if (suggestion.split(/\s+/).length > 4) return null;
  if (blockedSuggestionTerms.some((term) => lower.includes(term))) return null;
  if (!/[a-z]/i.test(suggestion)) return null;
  return suggestion;
}

export function mergeSuggestions(primary: string[], derived: string[], limit = 40): string[] {
  const seen = new Set<string>();
  return [...primary, ...derived]
    .map(cleanSuggestion)
    .filter((item): item is string => Boolean(item))
    .filter((item) => {
      const key = item.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((left, right) => left.localeCompare(right))
    .slice(0, limit);
}
