import {
  Lead,
  LeadInput,
  postDraft,
  postEnrich,
  postLog,
  postScore,
} from "@/lib/api";

export type PipelineStage = "enrich" | "score" | "draft" | "log" | "done";

export type RawLeadInput = {
  company_name: string;
  website_url: string;
  name: string;
  title: string | null;
  location: string | null;
  recent_signal: string | null;
};

/**
 * Runs one lead through enrich -> score -> draft -> log, same shape as
 * scripts/run_batch.py's build_lead_payload (enrichment wins for
 * company_size/industry), but calling /log too so it actually persists.
 */
export async function runLeadPipeline(
  input: RawLeadInput,
  onProgress: (stage: PipelineStage) => void,
): Promise<Lead> {
  onProgress("enrich");
  const enrichResult = await postEnrich({
    company_name: input.company_name,
    website_url: input.website_url,
  });

  const leadInput: LeadInput = {
    name: input.name,
    company: enrichResult.company_name,
    title: input.title,
    company_size: enrichResult.company_size,
    industry: enrichResult.industry,
    linkedin_active_recently: null,
    estimated_monthly_leads: null,
    has_dedicated_sales_role: null,
    recent_signal: input.recent_signal,
    location: input.location,
    phone: enrichResult.phone,
    social_links: enrichResult.social_links,
    website_url: enrichResult.website_url,
  };

  onProgress("score");
  const scoreResult = await postScore(leadInput);

  onProgress("draft");
  const draftResult = await postDraft({
    ...leadInput,
    score: scoreResult.score,
    confidence: scoreResult.confidence,
    reason: scoreResult.reason,
  });
  const draftedMessage = draftResult.drafted ? draftResult.message : null;

  onProgress("log");
  const logResult = await postLog({
    ...leadInput,
    score: scoreResult.score,
    confidence: scoreResult.confidence,
    reason: scoreResult.reason,
    drafted_message: draftedMessage,
  });

  onProgress("done");

  return {
    id: logResult.id,
    name: leadInput.name,
    company: leadInput.company,
    title: leadInput.title,
    company_size: enrichResult.company_size,
    industry: enrichResult.industry,
    linkedin_active_recently: leadInput.linkedin_active_recently,
    estimated_monthly_leads: leadInput.estimated_monthly_leads,
    has_dedicated_sales_role: leadInput.has_dedicated_sales_role,
    recent_signal: leadInput.recent_signal,
    location: leadInput.location,
    phone: leadInput.phone,
    social_links: leadInput.social_links,
    website_url: leadInput.website_url,
    score: scoreResult.score,
    confidence: scoreResult.confidence,
    reason: scoreResult.reason,
    drafted_message: draftedMessage,
    status: logResult.status,
    created_at: new Date().toISOString(),
  };
}
