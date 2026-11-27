// Zapier durable workflow 01a21a37-f799-7e23-8603-da1e488892ac
// "UTIP: New calendar event → Discord #events (+ Instagram fallback)"
// Trigger: Google Calendar "new_event" on the public UTIP calendar.
//
// Always posts to Discord #events. Also posts the generic Instagram feed post +
// story UNLESS the event description contains "Instagram: Canva" — the Officer
// Console writes that line when it is making a fresh Canva design for the event
// and posting it itself (so nothing is posted twice).
import { defineDurable } from "@zapier/zapier-durable";
import { createZapierSdk } from "@zapier/zapier-sdk";
import { z } from "zod";

const sdk = createZapierSdk();

const DISCORD = "DiscordCLIAPI";
const DISCORD_CONNECTION = "discord_utip";
const BUFFER_CONNECTION = "buffer_utip";
const IG_CHANNEL = "6b086b7c8541f09ecbb2d713"; // Buffer channel for @utip_austin
const EVENTS_CHANNEL = "1575567528351105064";
const MEMBER_ROLE = "1575567325023838290";
const LINKTREE = "https://linktr.ee/utip";
const TZ = "America/Chicago";
const STORY_IMAGE = "https://raw.githubusercontent.com/pe-tanman/utip_setup/7384870aa067a78cd528420666d29247a59c3aa1/exports/instagram/stories/story-event-generic-01.png";
const POST_IMAGE = "https://raw.githubusercontent.com/pe-tanman/utip_setup/6d35457ca62edb929ac8ba83185166a4fd1f82be/exports/instagram/post-event-generic.png";
const LOGO = "https://raw.githubusercontent.com/pe-tanman/utip_setup/a4e0204dcc98f5c160a84f268cc803f1d595f451/exports/instagram/profile-picture.png";
const HASHTAGS = "#UTAustin #UTIP #pickleball #internationalstudents #hookem #utaustinstudents #austinpickleball";
const CANVA_MARKER = /Instagram:\s*Canva/i;

// Google Calendar event. Only the fields we use are typed; start/end can be objects or flattened.
const InputSchema = z
  .object({
    summary: z.string().nullable().optional(),
    description: z.string().nullable().optional(),
    location: z.string().nullable().optional(),
    htmlLink: z.string().nullable().optional(),
    status: z.string().nullable().optional(),
    start: z.unknown().nullable().optional(),
    start__dateTime: z.string().nullable().optional(),
    start__date: z.string().nullable().optional(),
  })
  .loose();

function startIso(input: z.infer<typeof InputSchema>): string | null {
  const s = input.start as { dateTime?: string; date?: string } | string | null | undefined;
  if (typeof s === "string") return s;
  return s?.dateTime ?? input.start__dateTime ?? s?.date ?? input.start__date ?? null;
}

// First link in the description (a Luma page, a form...) is treated as the RSVP link.
function rsvpLink(description: string): string | null {
  const m = description.match(/https?:\/\/[^\s"'<>)]+/);
  return m ? m[0] : null;
}

function austinTime(ms: number): string | null {
  if (!Number.isFinite(ms)) return null;
  try {
    return new Intl.DateTimeFormat("en-US", { timeZone: TZ, weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(ms));
  } catch {
    return new Date(ms).toISOString();
  }
}

async function bufferCreatePost(input: Record<string, unknown>): Promise<string> {
  const res = await sdk.fetch("https://api.buffer.com/graphql", {
    connection: BUFFER_CONNECTION,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: "mutation($input: CreatePostInput!) { createPost(input: $input) { __typename } }",
      variables: { input },
    }),
  });
  const body = JSON.parse(await res.text());
  const typename = body?.data?.createPost?.__typename ?? null;
  if (res.status >= 400 || typename !== "PostActionSuccess") {
    throw new Error(`Buffer post failed (${res.status}): ${JSON.stringify(body).slice(0, 400)}`);
  }
  return typename;
}

const workflow = defineDurable({
  name: "utip-calendar-to-discord",
  inputSchema: InputSchema,
  run: async (ctx, rawInput) => {
    const input = InputSchema.parse(rawInput ?? {});
    if ((input.status ?? "").toLowerCase() === "cancelled") {
      return { skipped: true, reason: "cancelled-event" };
    }
    const title = (input.summary ?? "").trim() || "UTIP event";
    const iso = startIso(input);
    const ms = iso ? Date.parse(iso) : NaN;
    const when = Number.isFinite(ms)
      ? `<t:${Math.floor(ms / 1000)}:F> (<t:${Math.floor(ms / 1000)}:R>)`
      : (iso ?? "see calendar");
    const where = (input.location ?? "").trim();
    const rawDescription = (input.description ?? "").replace(/<br\s*\/?>/gi, "\n");
    const canvaHandled = CANVA_MARKER.test(rawDescription.replace(/<[^>]+>/g, " "));
    const rsvp = rsvpLink(rawDescription);
    const details = rawDescription
      .replace(/<[^>]+>/g, " ")
      .replace(/https?:\/\/[^\s"'<>)]+/g, "")
      .replace(/^\s*Instagram:.*$/gim, "")
      .replace(/^(RSVP|All links):?\s*$/gim, "")
      .replace(/[ \t]+/g, " ")
      .replace(/\n{3,}/g, "\n\n")
      .trim()
      .slice(0, 700);

    const lines = [
      `<@&${MEMBER_ROLE}> \u{1F4C5} **New UTIP event: ${title}**`,
      `\u{1F5D3} ${when}`,
      where ? `\u{1F4CD} ${where}` : null,
      details ? `\n${details}` : null,
      "",
      rsvp ? `\u{1F449} **RSVP:** <${rsvp}>` : null,
      `\u{2705} React with \u{2705} if you're coming so we book enough courts!`,
      input.htmlLink ? `Add to your calendar: <${input.htmlLink}>` : null,
      `All links: <${LINKTREE}>`,
    ].filter((l) => l !== null);

    const posted = await ctx.step("post-to-discord-events", async () =>
      sdk.runAction({
        appKey: DISCORD,
        actionType: "write",
        actionKey: "send_channel_message",
        connection: DISCORD_CONNECTION,
        inputs: {
          channel_id: EVENTS_CHANNEL,
          content: lines.join("\n").slice(0, 1990),
          ping_usernames: true,
          username: "UTIP Events",
          avatar_url: LOGO,
        },
      }),
    );

    const storyLink = rsvp ?? LINKTREE;
    let feed: string | null = null;
    let story: string | null = null;

    // Officer Console events get a fresh Canva design posted from the Console instead.
    if (!canvaHandled) {
      // Instagram feed post: generic "New event!" graphic, all details in the caption.
      const austin = austinTime(ms);
      const caption = [
        `\u{1F3D3} New UTIP event: ${title}`,
        "",
        austin ? `\u{1F4C5} ${austin} (Austin time)` : null,
        where ? `\u{1F4CD} ${where}` : null,
        details ? `\n${details.replace(/\n{2,}/g, "\n")}` : null,
        "",
        `\u{1F449} RSVP: ${rsvp ? rsvp.replace(/^https?:\/\//, "") : "linktr.ee/utip"} (link in bio + in our story)`,
        "International and domestic students, all levels welcome. Bring a friend!",
        "",
        HASHTAGS,
      ]
        .filter((l) => l !== null)
        .join("\n")
        .slice(0, 2100);
      feed = await ctx.step("post-instagram-feed", async () =>
        bufferCreatePost({
          channelId: IG_CHANNEL,
          schedulingType: "automatic",
          mode: "shareNow",
          needsApproval: false,
          text: caption,
          assets: [{ image: { url: POST_IMAGE, metadata: { altText: `New UTIP event: ${title}. Date, time and place are in the caption.` } } }],
          metadata: { instagram: { type: "post", shouldShareToFeed: true } },
        }),
      );

      // Instagram story with a link sticker.
      story = await ctx.step("post-instagram-story", async () =>
        bufferCreatePost({
          channelId: IG_CHANNEL,
          schedulingType: "automatic",
          mode: "shareNow",
          needsApproval: false,
          text: "",
          assets: [{ image: { url: STORY_IMAGE, metadata: { altText: `New UTIP event: ${title}. Tap the link for details and RSVP.` } } }],
          metadata: { instagram: { type: "story", shouldShareToFeed: false, link: storyLink } },
        }),
      );
    }

    return {
      posted: true,
      title,
      rsvp,
      storyLink,
      instagram: canvaHandled ? "posted-from-officer-console" : "generic-fallback",
      feed,
      story,
      messageId: (posted.data?.[0] as { id?: string } | undefined)?.id ?? null,
    };
  },
});

export default workflow;
