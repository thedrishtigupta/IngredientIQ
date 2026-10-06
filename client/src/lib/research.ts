/**
 * Research track results are produced offline by the modelling pipeline
 * (Model A vs Model B, SHAP). Nothing is displayed until those artefacts are
 * loaded — no placeholder numbers.
 */
export const researchStatus: {
  state: "pending" | "ready";
  modelComparison: null;
  associations: null;
  shap: null;
} = { state: "pending", modelComparison: null, associations: null, shap: null };
