export type BuyerJobPreview = {
  job_id: string;
  geo?: string;
  locale?: string;
  cta_id?: string;
  format?: string;
  status?: string;
  cta_main?: string;
  disclaimer?: string;
  blocked_reason?: string | null;
};

export type RunReportShape = {
  готово?: number;
  отсеяно?: number;
  гео_готово?: string[];
  гео_отсеяно?: { гео?: string; этап?: string; причина?: string }[];
  предупреждения?: { гео?: string; предупреждения?: string[] }[];
  ссылки?: {
    гео?: string;
    текст?: string;
    кегль?: string | number | null;
    файл?: string;
    filename?: string;
    qc_metrics?: Record<string, string | number | boolean | null>;
  }[];
  прогон?: {
    run_id?: string;
    run_hash?: string;
    day?: string;
    folder_id?: string;
    all_geos?: {
      geo?: string;
      qc_pass?: boolean;
      issues?: string[];
      warnings?: string[];
      qc_metrics?: Record<string, string | number | boolean | null>;
      filename?: string;
    }[];
  };
  отчёт_в_drive?: string | null;
  время?: string;
  analysis?: {
    analysis_id?: string;
    format?: string;
    status?: string;
    game_id?: string;
    product?: string;
    beats?: {
      beat_id: string;
      name?: string;
      t_start?: number;
      t_end?: number;
      duration_sec?: number;
      substitution_group?: string;
    }[];
  } | null;
  multiply?: {
    analysis_id?: string;
    jobs?: number;
    job_ids?: string[];
    geos?: string[];
    ctas?: string[];
    format?: string;
    duration_sec?: number;
    beats?: number;
    deep_job_id?: string | null;
    ready_jobs?: number;
    blocked_jobs?: number;
    ready_geos?: string[];
    blocked_geos?: string[];
    n8n_geos?: string[];
    n8n_skip_reason?: string | null;
    variants?: BuyerJobPreview[];
  } | null;
};
