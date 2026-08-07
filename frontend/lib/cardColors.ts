export type CardColorFamily = {
  name: string;
  /** Bold solid block used for the card's collapsed header. */
  card: string;
  cardText: string;
  cardTextMuted: string;
  /** Dusty mid-tone tint for the two pill badges — not white, ~2 shades lighter than `card`. */
  pillBg: string;
  pillText: string;
};

const CARD_COLOR_FAMILIES: CardColorFamily[] = [
  {
    name: "coral",
    card: "#E2725B",
    cardText: "#FFFFFF",
    cardTextMuted: "#F6D9CF",
    pillBg: "#EFB6A6",
    pillText: "#7A3520",
  },
  {
    name: "purple",
    card: "#8B6FB3",
    cardText: "#FFFFFF",
    cardTextMuted: "#E4DAF2",
    pillBg: "#D3C4E8",
    pillText: "#4A3670",
  },
  {
    name: "teal",
    card: "#3F9188",
    cardText: "#FFFFFF",
    cardTextMuted: "#CDE9E5",
    pillBg: "#A8D6CF",
    pillText: "#1D5850",
  },
];

/** Deterministic per-lead color so a card's color never changes across sorts/filters/re-renders. */
export function getCardColors(leadId: number): CardColorFamily {
  const index = ((leadId % CARD_COLOR_FAMILIES.length) + CARD_COLOR_FAMILIES.length) % CARD_COLOR_FAMILIES.length;
  return CARD_COLOR_FAMILIES[index];
}
