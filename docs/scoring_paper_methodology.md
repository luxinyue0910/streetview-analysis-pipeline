# Methods: Frozen vision-language and visual-feature scoring of paired street views

**Paper-methods draft and mathematical implementation supplement.** This describes
what the frozen scorer actually did, rather than proposing another experiment.
Prepared October 25, 2026 (America/Los_Angeles). The manuscript-style methods are
Sections 1–8; the target-specific configuration and implementation audit follow
in Appendices A–D. The original scoring records, fitted models, and data are
unchanged by this documentation update.

## 1. Study images and prediction targets

The source street-view collection contained 105,180 images from 26,295 locations
across four road levels. Exact coordinate matching to the study-area list retained
13,660 locations, each with four directional images (54,640 images). An earlier
image-selection stage used frozen CLIP features with a lightweight classifier,
opposing-direction pair constraints, and confirmed selection overrides to retain
two side-facing views per location. The resulting manifest contains 27,320 image
references. Image selection and subsequent quality scoring are separate stages;
the CLIP selection classifier is not the scoring regression model. Details of
selection and its evaluation are archived in the [selection methods](methodology.md)
and [selection milestone](milestone_2026-10-13.md).

We predicted four dimensions—pedestrian safety, street interface, greenery/staying,
and environmental maintenance—at three scopes: overall, Side A, and Side B. This
yields 12 scalar targets in [0,1] per location. Scope precedes dimension in the
column order, as listed in Appendix A. Overall quality was scored from both images
independently; it was not calculated as the average of the two side scores.

For scoring, Side A was the selected image with angle 0° or 90°, and Side B was
the selected image with angle 180° or 270°. These are canonical angle identities,
not geographical left/right labels. Where source slots were reversed, image
paths, cached side-specific Flash scores, visual feature rows, and the four
corresponding reference columns were permuted together. This operation preserved
the source image-to-label association; it did not infer how a historical annotator
visually intended A/B and did not minimize prediction error against reference
scores. Overall references and symmetric overall visual features were unchanged.
Cached overall development Flash scores were retained, without claiming that
cloud VLM responses are mathematically invariant to image order.

## 2. Reference data and development design

The accepted team reference table was used as supplied as the supervised target.
Of the original 1,000 listed development/reference locations, 773 had usable numeric
scores and 227 had all-NA references. A previously reserved 200-location set was
kept separate. From the remaining 573-location development pool, 85 locations
sharing spatial groups with that reserved set were isolated, leaving **488
locations in 400 groups** for model development and final fitting. Groups followed
the frozen spatial metadata: 500 m grid grouping with unions of locations within
100 m and locations sharing byte-identical images. Group separation does not
establish that every road or wider neighborhood is disjoint.

We reused five spatial outer folds and four spatial inner folds within each outer
training partition. Each outer fold held out 97 or 98 locations; preprocessing
and candidate fitting used only that fold's training data. Imputation, feature
scaling, PCA, score-band weights, and fitted estimators were not fitted on the
outer evaluation partition. Reference scores were never inference features.
Prompt development and repeated method comparisons nevertheless exposed the
development labels; nested CV therefore constitutes development evidence rather
than a fresh blinded test of the entire prompt-discovery process.

The 12 targets are correlated measurements at a location, not 12 independent
training examples. Accepted reference values, including averaged/intermediate
levels such as 0.3 and 0.7 in development, were retained without snapping them to
the VLM's original rubric anchors. NA references were excluded from eligibility
rather than changed to zero. The frozen training set has numeric labels for all
12 targets. This report makes no additional claim of independent human annotation
provenance beyond the accepted reference records.

## 3. VLM scoring and visual representation

### 3.1. Flash initial scores

We used `qwen3.8-flash` through the DashScope Beijing compatible chat endpoint,
with the complete organized v2 rubric prompt, temperature 0, thinking disabled,
JSON-object output, and a maximum of 900 output tokens. Each location required
three requests: both images in canonical A-then-B order for overall quality,
only A for Side A, and only B for Side B. Explicit side, angle, and filename text
accompanied each image. Original PNG bytes were supplied without a new region-of-
interest crop. No reference scores or worked reference examples were supplied.

Each response returned four rubric scores and one short evidence string per
dimension (at most 40 characters). The evidence strings were retained for audit
but were not supervised-model features. The permitted raw score set was

$$
\mathcal A=\{0,0.1,0.2,0.4,0.5,0.6,0.8,0.9,1\},
\qquad q_{i,s,d}\in\mathcal A\cup\{\mathrm{NA}\}. \tag{1}
$$

Flash returned scores directly, **not a distribution over score levels**. Later
probabilities came from a local supervised classifier. Lossless numeric strings
at legal anchors were accepted while preserving the raw response. Public prompt
fragments require the private PDF-derived rubric; the exact static full-prompt
hashes and request settings are recorded in the [frozen configuration](../configs/scoring/flash_v2_dino_canonical_frozen.json).
No finer provider backend snapshot identifier was available; temperature 0 does
not guarantee identical responses if the hosted backend changes.

### 3.2. Frozen DINOv2 features

We used frozen `facebook/dinov2-small` at revision
`ed25f3a31f01632728cabb09d1542f84ab7b0056` on CPU. DINOv2 provides pretrained
visual representations [1]. EXIF orientation was applied and images were converted
to RGB. The shortest side was scaled to 224 pixels, each resulting dimension was
rounded to a multiple of 14, and bicubic interpolation was used, without cropping.
RGB values were divided by 255 and normalized with mean (0.485, 0.456, 0.406) and
standard deviation (0.229, 0.224, 0.225).

Let $v_{i,A},v_{i,B}\in\mathbb R^{384}$ be final-layer CLS features. The scope
representations were

$$
v_{i,O}=\left[\frac{v_{i,A}+v_{i,B}}{2},\ |v_{i,A}-v_{i,B}|\right],
\qquad v_{i,s}=v_{i,A}\ \text{or}\ v_{i,B}\quad(s=A,B). \tag{2}
$$

The overall representation has 768 dimensions; side representations have 384.
Grid-enabled safety modules also concatenate CLS with six mean-pooled patch-token
cells in a 2×3 spatial grid, ordered by row then column. Each image then has
$384+6\times384=2,688$ dimensions; the overall mean/difference representation has
5,376. Cell boundaries are integer indices from equally spaced grid boundaries;
cell means are accumulated in float64 then stored as float32. Neither DINOv2 nor
Flash was fine-tuned.

For scope $s$, define the four raw Flash scores $q_{i,s}$ and four missing indicators
$m_{i,s,d}=\mathbf 1\{q_{i,s,d}\text{ is nonfinite}\}$. Ridge fusion input was

$$
x^{R}_{i,s}=\operatorname{Scale}_T\!\left(
 \operatorname{Impute}_T[\,v_{i,s},q_{i,s},m_{i,s}\,]\right). \tag{3}
$$

Here $T$ is the active training partition and $\operatorname{Impute}_T$ uses
training-column medians, retaining empty columns. Base Ridge preprocessing was
median imputation followed by standard scaling; it did **not** use image PCA.
DINO-only Ridge used the corresponding visual representation alone. SVR,
score-probability classifiers, and safety modules used a separate transform:

$$
x^{P}_{i,s}=\operatorname{Scale}^{\rm joint}_T\left[
 \operatorname{PCA}_{20,T}(\operatorname{Scale}^{\rm image}_T(v_{i,s})),
 \operatorname{Impute}_T(q_{i,s},m_{i,s})\right]. \tag{4}
$$

PCA used the randomized solver with seed 42. For safety, $v$ in Eq. 4 is CLS or
CLS-plus-grid according to Appendix A. All transforms were saved and reused
unchanged at inference.

## 4. Target-specific supervised mixture

A separate model tree was selected for each target $j=(s,d)$. Define
$\Pi_{[a,b]}(t)=\min(b,\max(a,t))$. Individual regression and calibration outputs
were clipped to [0,1] before blending.

### 4.1. Ridge and calibration components

The Ridge component minimized weighted squared error with an unpenalized intercept:

$$
(\hat\theta_j,\hat b_j)=\arg\min_{\theta,b}
 \sum_{i\in T}w_{i,j}(y_{i,j}-b-\theta^\top x_{i,s})^2
 +\lambda_j\|\theta\|_2^2,
\qquad f_j(x)=\Pi_{[0,1]}(\hat b_j+\hat\theta_j^\top x). \tag{5}
$$

Both unweighted and score-band-weighted candidates were considered. Bands were
low ($y\le0.3$), middle ($0.3<y<0.8$), and high ($y\ge0.8$). With training counts
$n_b$ and $n_{\max}=\max_b n_b$, weights for observed-band rows were

$$
\tilde w_{i,j}=\min\{3,(n_{\max}/n_{b(y_{i,j})})^{\rho_j}\},
\qquad w_{i,j}=\tilde w_{i,j}\big/\left(|T|^{-1}\sum_{r\in T}\tilde w_{r,j}\right),
\qquad \rho_j\in\{0,0.5,1\}. \tag{6}
$$

The base fusion Ridge used $\rho=0$. Ridge alpha candidates were 1, 10, 100,
1,000, and 10,000. Other first-stage candidates were raw Flash, nonnegative-slope
affine calibration, isotonic calibration constrained to [0,1], and DINO-only Ridge.
Affine and isotonic calibration used numeric Flash rows only; at inference a
missing raw score used that component's training-reference mean. If calibration
could not be fitted, the same mean fallback applied. Fusion models instead used
training-fitted imputation and missing indicators. NA was not a zero-valued label.

The first-stage prediction blended the selected unweighted fusion Ridge $f_j$
and candidate $g_j$:

$$
R_{i,j}=(1-a_j)f_j(x_{i,s})+a_jg_j(x_{i,s}),
\qquad a_j\in\{0,0.25,0.5,0.75,1\}. \tag{7}
$$

For a calibration/raw component, $g_j$ uses the relevant Flash score rather than
the complete image vector. The notation represents the saved model tree, not a
single globally shared formula or weight.

### 4.2. Score-probability decoder

A local L2-regularized logistic classifier predicted probabilities on the fixed
11-level support $c_k=k/10$, $k=0,\ldots,10$. The fitting code converts one-decimal
reference values to class indices with `rint(10*y)` and asserts reconstruction of
the original numeric labels. It does not replace accepted references with the
nine raw VLM anchors. For observed classes, the multinomial logistic form is

$$
p_{i,j,k}=\frac{\exp(\eta_{j,k}^\top x^{P}_{i,s}+b_{j,k})}
 {\sum_{\ell\in\mathcal C_{T,j}}\exp(\eta_{j,\ell}^\top x^{P}_{i,s}+b_{j,\ell})},
\quad k\in\mathcal C_{T,j};
\qquad p_{i,j,k}=0\ \text{for unobserved classes}. \tag{8}
$$

The saved classifier's `predict_proba` supplies these values; a single-class
training partition is represented by a point mass. The final retained probability
components all use logistic regression (`lbfgs`, at most 2,000 iterations,
tolerance $10^{-7}$); their inverse-regularization parameters $C$ are listed in
Appendix A. These are score-class probabilities, not independently validated
confidence estimates.

Two decoders were compared. Probability-mean decoding is

$$
D^{\rm mean}_{i,j}=\Pi_{[0,1]}\left(\sum_{k=0}^{10}p_{i,j,k}c_k\right). \tag{9}
$$

Window decoding chooses a continuous center with high predicted smoothed mass
within a ±0.1 interval:

$$
M_{i,j}(z;\sigma_j)=\sum_{k=0}^{10}p_{i,j,k}
 \left[\Phi\!\left(\frac{z+0.1-c_k}{\sigma_j}\right)
       -\Phi\!\left(\frac{z-0.1-c_k}{\sigma_j}\right)\right],
\qquad D^{\rm win}_{i,j}\ \approx\ \arg\max_{z\in[0,1]}M_{i,j}(z;\sigma_j). \tag{10}
$$

$\Phi$ is the standard normal CDF. The approximation symbol is intentional:
implementation evaluates 201 centers spaced by 0.005, selects the first grid
maximum, refines within ±0.01 of that center using bounded scalar minimization
of $-M$ (`xatol=1e-10`), and chooses the best of the refined center and the two
local endpoints. It does not certify a global continuous optimum. Candidate
bandwidths were 0.05, 0.10, and 0.15. This decoder is a tolerance-oriented decision
rule, not probability-mean averaging or an uncertainty interval.

### 4.3. SVR and staged blending

RBF epsilon-SVR supplied a clipped candidate $h_j(x^P)$, using the standard
objective $\frac12\|w\|^2+C\sum_i\max(0,|y_i-h(x_i)|-\epsilon)$ and kernel
$K(x,x')=\exp(-\gamma\|x-x'\|^2)$ [3]. Candidate grids used
$C\in\{0.1,1,10\}$, $\epsilon\in\{0.02,0.05,0.1\}$, and
$\gamma\in\{\texttt{scale},0.01,0.1\}$. For `scale`, the library uses
$1/(n_{\rm features}\operatorname{Var}(X_T))$ on the transformed training matrix.
The staged predictions were

$$
T_{i,j}=(1-b_j)R_{i,j}+b_j\Pi_{[0,1]}(h_j(x^{P}_{i,s})), \tag{11}
$$

$$
B_{i,j}=(1-c_j)T_{i,j}+c_jD_{i,j},
\qquad b_j,c_j\in\{0,0.25,0.5,0.75,1\}. \tag{12}
$$

Absent stages have weight zero and are skipped. The selection pool also allowed
the tolerance stage to retain an alternative first-stage blend; the *actual final
12 fitted trees* in Appendix A all resolve to the displayed structure. Three
maintenance targets and B-side street interface have no SVR or probability stage.
Eight targets retain a probability decoder: three mean and five window decoders.
A weight of 1 can remove earlier stages' numerical influence even though those
stages remain stored in the model tree. For example, overall safety uses an SVR
weight of 1; its stored first-stage Ridge blend does not affect the base result.

## 5. Low-safety routing and expert correction

Only pedestrian safety at overall/A/B scopes received an additional module. For
training, $\ell_{i,j}=\mathbf1\{y_{i,j}\le0.3\}$. The routing classifier used all
active training rows, with the same-scope features from Eq. 4. Training rows with
non-low references but low raw Flash safety scores were treated as hard negatives:

$$
\omega_{i,j}=\begin{cases}
2,&y_{i,j}>0.3,\ q_{i,j}\text{ numeric},\ q_{i,j}\le0.3,\\
1,&\text{otherwise}.
\end{cases} \tag{13}
$$

Balanced class weighting was applied in addition to these sample weights. The
final overall and A-side gates used logistic regression ($C=0.01$); B-side used
histogram gradient boosting (100 iterations, learning rate 0.05, at most seven
leaf nodes, minimum leaf size 20, L2 regularization 10, early stopping disabled,
seed 42). For logistic gates, the positive-class score is the sigmoid of the saved
linear predictor; the histogram gate uses the saved boosted-tree positive-class
probability. Gate outputs are uncalibrated routing scores.

For each safety scope, a separate Ridge expert $e_j$ was fitted **only** on
reference-low rows, using the transform fitted on the entire active training
partition. Its raw prediction was clipped to [0,0.3]. Routing and replacement were

$$
r_{i,j}=\mathbf1\{g^{\rm low}_j(x^P_{i,s})\ge\tau_j\},
\qquad E_{i,j}=\Pi_{[0,0.3]}(e_j(x^P_{i,s})), \tag{14}
$$

$$
z_{i,j}=\begin{cases}
E_{i,j},&j\text{ is safety and }r_{i,j}=1,\\
B_{i,j},&\text{otherwise}.
\end{cases} \tag{15}
$$

The threshold was selected using development folds and held fixed for new
locations. It was not determined from a new location's reference or the final
score being below 0.3. The other nine targets remained exactly equal to $B$.
This was hard replacement with a learned expert, not automatic subtraction of a
constant or a reference-guided low-score adjustment. Final thresholds, feature
choices, and expert alphas appear in Appendix A.

## 6. Candidate selection, final fitting, and score precision

Within each active training partition, candidate predictions were collected on
spatially held-out inner rows. Base fusion alpha was selected by MAE. First-stage
blend selection minimized $0.7\,\mathrm{MAE}+0.3\,\mathrm{mean}(\mathrm{MAE}_{\rm low},
\mathrm{MAE}_{\rm mid},\mathrm{MAE}_{\rm high})$, excluding empty bands. It allowed
at most +0.005 overall MAE and +0.005 large-error rate versus the selected base;
when a band had at least 20 rows, low-band MAE could not increase and high-band
MAE could increase by at most 0.005. Ties used MAE then candidate order.

The SVR and probability stages prioritized within-0.1 hit rate on continuous inner
predictions, with guards versus the preceding baseline: overall MAE increase at
most 0.003, large-error rate increase at most 0.005, and low/high-band MAE increase
at most 0.005 when at least 20 rows were available. Ties used MAE, large-error
rate, and candidate order. Exact baseline candidates remained available.

Safety-wrapper selection used uniformly one-decimal inner predictions and
prioritized low-reference within-0.1 hit rate (overall hit if fewer than ten low
rows). Relative to the base, guards allowed at most 0.02 overall hit-rate decrease,
0.003 overall MAE increase, no increase in large-error count, 0.01 non-low hit-rate
decrease, 0.003 non-low MAE increase, and 0.005 low-band MAE increase. Ties used
low MAE, overall hit, non-low MAE, large-error count, then candidate order. These
are selection safeguards, not guarantees on later evaluation rows. The final
canonical refit did increase development OOF rounded large errors relative to the
previous noncanonical fit (268 to 284); this tradeoff was retained for consistent
identity and is documented in the [freeze report](scoring_frozen_2026-10-25.md).

After development selection, final component choices used five spatial folds
across the full development set, and each selected estimator and preprocessing
transform was refitted on all 488 development locations. The resulting scorer
was **not** an ensemble average of the five outer-fold models. The final freeze
was recorded on October 24, 2026 at 02:26 UTC; validation predictions were sealed
at 03:23 UTC before comparison with the validation reference. No validation
reference entered prompt/parameter selection or fitting. The same fitted freeze
was subsequently reused for all 12,160 remaining locations, without retraining.

Each final continuous prediction $z_{i,j}\in[0,1]$ was retained. The selected
one-decimal delivery used uniform half-up rounding for every target:

$$
s_{i,j}=\frac{\lfloor10z_{i,j}+0.5\rfloor}{10}. \tag{16}
$$

This is the archived NumPy arithmetic, not Python's tie-to-even `round`. There
was no target- or error-dependent rounding. The score represents a continuous
estimate of the accepted reference followed by one-decimal reporting; it is not
restricted to the original nine rubric anchors. Thus 0.3 and 0.7 are valid outputs
of this scheme, even where the raw Flash anchors omit them. Rounding policy was
already fixed before the 500-location validation. Continuous predictions remained
the primary evaluation precision; one-decimal delivery remained secondary.

## 7. Validation and paired-side analysis

The held-out 500-location list was scored using the frozen model before its
accepted reference table was evaluated. There were 405 locations with all 12
numeric references (4,860 score items); 95 had all-NA references and were excluded
from error metrics but retained in prediction delivery. Seventeen raw Flash items
were NA on numeric references. We reported both each method's numeric coverage
and a matched comparison on the 4,843 items where raw Flash was numeric.

Point IDs were disjoint between development and validation. A byte-level audit
found four image hashes shared at two validation locations; those locations were
retained. The validation therefore has a known image-overlap limitation and is
not perfectly image-disjoint. No overlap-excluded estimate is claimed. The older
200-location evaluation applies to a historical base, not the final canonical
low-safety extension, and is not presented as a second test of this final model.

For numeric prediction/reference pairs in evaluation set $\mathcal E$, error was
$e_{i,j}=\hat y_{i,j}-y_{i,j}$. We reported

$$
\mathrm{MAE}=\frac1{|\mathcal E|}\sum_{(i,j)\in\mathcal E}|e_{i,j}|,
\quad \mathrm{RMSE}=\sqrt{\frac1{|\mathcal E|}\sum_{(i,j)\in\mathcal E}e_{i,j}^{2}},
\quad \mathrm{Bias}=\frac1{|\mathcal E|}\sum_{(i,j)\in\mathcal E}e_{i,j}, \tag{17}
$$

$$
H_{0.1}=\frac1{|\mathcal E|}\sum_{(i,j)\in\mathcal E}\mathbf1\{|e_{i,j}|\le0.1\},
\qquad L_{0.3}=\frac1{|\mathcal E|}\sum_{(i,j)\in\mathcal E}\mathbf1\{|e_{i,j}|\ge0.3\}. \tag{18}
$$

Thresholds are inclusive, with numerical evaluation tolerances `<=0.10000001`
and `>=0.29999999`. $H_{0.1}$ is an empirical agreement proportion, not exact-match
accuracy or a confidence probability. The same equations apply separately to
continuous and rounded predictions without rounding the reference. Dimension
summaries pool their three scopes; per-target metrics retain all 12 targets.
CCC, ICC(A,1), and Spearman correlation were calculated target-wise in development
and historical test diagnostics (Appendix C); they must not be inferred from the
aggregate tolerance hit rate. Where spatial-bootstrap intervals were reported,
3,000 group resamples with seed 42 kept predictions fixed, excluding model-refit
and cloud-repeat uncertainty. No new bootstrap results are introduced here.

Full coverage of 12,160 locations (145,920 scores per precision) demonstrates
completion and correspondence, not accuracy without reference. For paired-side
analysis, define signed and absolute differences for dimension $d$:

$$
\Delta_{i,d}=s_{i,A,d}-s_{i,B,d},
\qquad G_{i,d}=|\Delta_{i,d}|. \tag{19}
$$

The signed gap follows angle identity and is not a universal compass-direction
contrast. A large paired-side gap $G\ge0.3$ is a difference between modeled sides; it is not
the same event as model-reference error $|e|\ge0.3$. Continuous and rounded gap
analyses should be distinguished. Single-score agreement does not establish
accuracy of gap detection or a causal relationship with street design. Variance
compression in learned predictions, particularly greenery and maintenance,
should be considered in formal spatial or paired-side statistics.

## 8. Reference-guided A/B exchange: diagnostic only

A separate diagnostic asked whether matching opposite-side labels could reduce
large discrepancies. For each location and dimension independently, compare

$$
C^{\rm keep}_{i,d}=\mathbf1\{|s_{i,A,d}-y_{i,A,d}|\ge0.3\}
                 +\mathbf1\{|s_{i,B,d}-y_{i,B,d}|\ge0.3\},
$$

$$
C^{\rm swap}_{i,d}=\mathbf1\{|s_{i,B,d}-y_{i,A,d}|\ge0.3\}
                 +\mathbf1\{|s_{i,A,d}-y_{i,B,d}|\ge0.3\}. \tag{20}
$$

Exchange the two predictions for that dimension **only if**
$C^{\rm swap}_{i,d}<C^{\rm keep}_{i,d}$; leave ties unchanged. This includes
2→1, 2→0, and 1→0 improvements. Overall scores are untouched. Missing-reference
pairs are not eligible. Because this uses the reference, it is an oracle-style
matching diagnostic, not an inference algorithm, proof of annotation reversal,
or a valid replacement for fixed-identity validation. Independent swaps can also
assign different dimensions at one location to different source sides, so they
do not establish a coherent physical side identity. The 500-location and full
prediction deliveries never apply this diagnostic. See the [separate diagnostic
record](ab_dimension_diagnostic_2026-10-25.md).

## Appendix A. Exact correspondence to the 12 frozen model trees

The authoritative configuration is
[`flash_v2_dino_canonical_frozen.json`](../configs/scoring/flash_v2_dino_canonical_frozen.json).
The tables below are generated from its `base_structures` and `safety_models`,
not reconstructed from reported performance. Every target has its own fitted
coefficients even when hyperparameters coincide. These tables record the actual
final fit; fold-specific development selections can differ.

### A1. First-stage blend (Eq. 7)

`F(lambda,rho)` denotes fusion Ridge in Eqs. 3, 5–6. `Q` denotes raw Flash with
training-mean fallback for NA; `Iso(Q)` denotes fitted isotonic calibration with
the same missing-score fallback. The table's $a$ is the saved first-stage weight,
not the score-band exponent $\rho$.

| Target / output column | Base $f$ | Candidate $g$ | $a$ |
|---|---|---|---:|
| `overall_pedestrian_safety` | F(1000,0) | F(1000,1) | 1 |
| `overall_street_interface` | F(1000,0) | Q | 0.5 |
| `overall_greenery_staying` | F(1000,0) | Q | 0.25 |
| `overall_environmental_maintenance` | F(1000,0) | Iso(Q) | 0.75 |
| `side_A_pedestrian_safety` | F(100,0) | F(1000,0.5) | 0.25 |
| `side_A_street_interface` | F(100,0) | Q | 0.5 |
| `side_A_greenery_staying` | F(100,0) | F(100,1) | 0.5 |
| `side_A_environmental_maintenance` | F(1000,0) | Iso(Q) | 1 |
| `side_B_pedestrian_safety` | F(1000,0) | F(1000,0.5) | 0.75 |
| `side_B_street_interface` | F(1000,0) | Q | 0.5 |
| `side_B_greenery_staying` | F(1000,0) | F(100,1) | 0.5 |
| `side_B_environmental_maintenance` | F(1000,0) | Iso(Q) | 1 |

### A2. SVR and probability stages (Eqs. 8–12)

All retained SVRs use RBF kernels and $C=1$. A dash denotes a skipped stage
(weight zero), not a missing prediction. `W(sigma)` is Eq. 10; `Mean` is Eq. 9.
`C_prob` is the local logistic classifier parameter, not the SVR parameter.

| Target | $b$ | SVR epsilon | SVR gamma | $c$ | C_prob | Decoder |
|---|---:|---:|---|---:|---:|---|
| `overall_pedestrian_safety` | 1 | 0.05 | 0.01 | 0.25 | 10.0 | W(0.05) |
| `overall_street_interface` | 0.5 | 0.02 | 0.01 | 0.5 | 1.0 | W(0.1) |
| `overall_greenery_staying` | 0.25 | 0.02 | 0.01 | 0.75 | 10.0 | W(0.1) |
| `overall_environmental_maintenance` | 0 | — | — | 0 | — | — |
| `side_A_pedestrian_safety` | 0.5 | 0.02 | 0.01 | 0.25 | 1.0 | Mean |
| `side_A_street_interface` | 0.25 | 0.02 | 0.01 | 0.5 | 10.0 | Mean |
| `side_A_greenery_staying` | 0.5 | 0.02 | scale | 0.5 | 10.0 | W(0.15) |
| `side_A_environmental_maintenance` | 0 | — | — | 0 | — | — |
| `side_B_pedestrian_safety` | 0.75 | 0.05 | 0.01 | 0.75 | 1.0 | W(0.15) |
| `side_B_street_interface` | 0 | — | — | 0 | — | — |
| `side_B_greenery_staying` | 0.75 | 0.05 | 0.01 | 0.5 | 10.0 | Mean |
| `side_B_environmental_maintenance` | 0 | — | — | 0 | — | — |

### A3. Low-safety module (Eqs. 13–15)

All three use 20 image PCA components, balanced class weights, and hard-negative
sample weight 2. `Grid` means CLS plus 2×3 patch-cell means, not cropped-image
inference. Non-safety targets have no routing/expert stage.

| Target | Visual input | Gate | Threshold $\tau$ | Expert Ridge alpha | Low training rows |
|---|---|---|---:|---:|---:|
| `overall_pedestrian_safety` | grid | Logistic, C=0.01 | 0.6 | 100 | 69 |
| `side_A_pedestrian_safety` | cls | Logistic, C=0.01 | 0.7 | 100 | 74 |
| `side_B_pedestrian_safety` | grid | Histogram boosting, max leaves=7, L2=10 | 0.7 | 1000 | 82 |

### A4. Worked tree, not an illustrative global average

For `side_A_pedestrian_safety`, the stored model gives

$$
R=0.75F(100,0)+0.25F(1000,0.5),\quad
T=0.5R+0.5\operatorname{SVR}_{C=1,\epsilon=0.02,\gamma=0.01}(x^P),
\quad B=0.75T+0.25\sum_{k=0}^{10}p_kc_k. \tag{21}
$$

The individual regression predictions are clipped as above. If the separate
A-safety logistic gate is at least 0.7, replace $B$ with its low-only Ridge expert
(alpha 100, unit sample weights) clipped to [0,0.3]; otherwise keep $B$. Only then apply Eq. 16.
This example traces the actual A-safety tree and is not a prescription to use
these weights for other targets.

## Appendix B. Executable equation reference and archived source correspondence

[`scripts/scoring_frozen_reference.py`](../scripts/scoring_frozen_reference.py)
is a read-only publication companion extracted from the actual inference logic.
It accepts already-fitted estimator objects and aligned input arrays. It contains
no fitting, API request, filesystem write, or private data loader, and is **not
wired into the production workflow**. Publishing it does not alter the frozen
models, old predictions, or feature preprocessing. It requires NumPy and SciPy;
the supplied fitted estimators additionally require their compatible scikit-learn
runtime. Estimator coefficients and private arrays are not distributed.

The [formula audit](../results/scoring_2026-10-25/methodology_formula_audit.json)
verified all 12 stored model trees and three safety wrappers against the public
configuration. Replaying the existing 500 validation points reproduced all 6,000
continuous and rounded values exactly. A separate 20-point full-batch replay
reproduced all 240 rounded values exactly; continuous differences were at most
1.11e-16 from batch-shape floating-point arithmetic (checked tolerance 1e-12).
The decoder matched the archived implementation on 41 probability vectors under
all four decoder settings. These are implementation-parity checks, not a new
performance experiment; no reference labels were loaded. All 51 protected model,
freeze, delivery, and configuration files remained unchanged.

| Equations | Public reference function | Frozen JSON fields |
|---|---|---|
| 2 | [`visual_scopes`](../scripts/scoring_frozen_reference.py#L17) | `dino.overall_scope`, `dino.side_scope` |
| 3, 5–7 | [`predict_component`](../scripts/scoring_frozen_reference.py#L74), [`predict_base`](../scripts/scoring_frozen_reference.py#L99) | `base_structures[].structure`, recursively `base_model`, `candidate_model`, `weight`, `cfg.alpha`, `cfg.beta` |
| 4 | [`pca_features`](../scripts/scoring_frozen_reference.py#L63) and saved safety preprocessing | fitted preprocessing is private; feature design under `dino` and `safety_models[].image_pca_components` |
| 8 | [`score_probabilities`](../scripts/scoring_frozen_reference.py#L51) | probability node `classifier.parameters.C` |
| 9–10 | [`decode_probabilities`](../scripts/scoring_frozen_reference.py#L23) | probability node `decoder.kind`, `decoder.sigma` |
| 11 | [`predict_base`](../scripts/scoring_frozen_reference.py#L99) with `kind=svr` | SVR node `weight`, `regressor.parameters` |
| 12 | [`predict_base`](../scripts/scoring_frozen_reference.py#L99) with `kind=probability_mix` | probability node `weight`, `classifier`, `decoder` |
| 13 | training-only; sample-weight definition in Section 5 | `safety_models[].classifier_config.hard_negative_weight` |
| 14–15 | [`apply_safety_expert`](../scripts/scoring_frozen_reference.py#L118), [`predict_frozen`](../scripts/scoring_frozen_reference.py#L143) | `safety_models[].selected.threshold`, `expert.parameters.alpha`, `classifier_config` |
| 16 | [`round_one_decimal`](../scripts/scoring_frozen_reference.py#L138) | `rounding` |
| 17–20 | evaluation/diagnostic definitions, not inference features | separate aggregate validation and diagnostic records |

The original private source snapshots below were read to verify these formulas.
Only neutral filenames, function names, and file hashes are included here;
no local machine paths or per-location records are published. SHA-256 identifies
the exact source examined, rather than an executable dependency downloaded by
the reference module.

| Archived source | Functions / purpose | SHA-256 |
|---|---|---|
| `flash_v2_v6_dino_groupcv488_20261023T045922Z__train_comparison.py` | `features_for`, `prep_for`, `weights`, `fit_predict`, `choose`: base inputs, Ridge and calibration fitting/selection | `88894eb73f1b6bded458ec8d66ad7bab6e59006e00ccf01d7521591c63f75203` |
| `tolerance_hit_rate_groupcv488_20261023T052500Z__run.py` | `svrprep`, `svrx`, `choose`: PCA representation and tolerance guards | `a5f32670d9bb6721247edf39925a33dd3b5b0df857cda026a59ce0ed9f2ff336` |
| `probability_continuous_groupcv488_20261023T053257Z__run.py` | `fit_classifier`, `predict_proba`, `decode`: score classes and window optimization | `d95638511b511adfa5916993897e674e6b95581682b6d13aa60fda2bd6016bb0` |
| `frozen_mixture_test200_20261023T054421Z__train_final.py` | `train`: target-wise selection and full-development refit | `e15f0a7d4b7a1f1ce1517e8607695832abf8cabe15cfd30e2f23b7c735ddef38` |
| `frozen_mixture_test200_20261023T054421Z__predict_test.py` | `component`, `pca_features`, `predict`: recursive fitted-model inference | `5ea53aaa92ab891a85823e57fce6e65a1a5b1000bf332d127246dcd091b24205` |
| `train.py` | `preprocess`, `fit_classifier`, `expert`, `select`: low-safety training and selection | `7747927a2bb39c7fa2f12260dc223402cd244d78189d702b9faafa4e78827c76` |
| `workflow.py` | `prep`, `context`, `train`: canonical input normalization and final frozen fit | `fa92add4a7500f00614c07c0e88e8fe3f08a9e075679afe485e8f54f46c39ee7` |
| `inference.py` | `features`, `predict`: actual batch image features, safety replacement and rounding | `5e1ac8a82cdcb85c9e2d2f09bf38eea7eb3c441032732a3595818a4074326d0f` |

The final 19-file model-freeze manifest (15 fitted model files plus selection,
protocol, and workflow records) has SHA-256
`acb1db4dd55d768ac9fcdd4553706ef719c18ff8ec3831ce4aa4c66faadf481a`.
Validation and full inference reused that same freeze. Individual artifact hashes
are in `frozen_artifact_sha256` in the public JSON. The older snapshot filenames
identify reused function origins, not a claim that the final results came from
the historical 200-point model.

## Appendix C. Additional agreement statistics

For each target, with finite paired values $y$ and $p$, population means,
variances, and covariance give Lin's concordance correlation coefficient:

$$
\operatorname{CCC}_j=
\frac{2\operatorname{Cov}(y_j,p_j)}
 {\operatorname{Var}(y_j)+\operatorname{Var}(p_j)+(\bar y_j-\bar p_j)^2}. \tag{22}
$$

Variance and covariance use denominator $n$, matching the archived implementation.
A near-zero denominator returns an undefined result. Macro-target CCC averages
valid target-specific coefficients; pooled cross-target CCC is not evidence of
within-dimension discrimination. Spearman correlation is Pearson correlation of
average ranks and is undefined for constant inputs in the archived metric code.

For the two-column matrix $Z=[y,p]$, with row means $\bar Z_{i\cdot}$, column
means $\bar Z_{\cdot c}$, and grand mean $\bar Z$, the two-way absolute-agreement,
single-measurement statistic uses

$$
MS_R=\frac{2}{n-1}\sum_i(\bar Z_{i\cdot}-\bar Z)^2,\quad
MS_C=n\sum_{c=1}^2(\bar Z_{\cdot c}-\bar Z)^2,
$$

$$
MS_E=\frac1{n-1}\sum_{i,c}
 (Z_{ic}-\bar Z_{i\cdot}-\bar Z_{\cdot c}+\bar Z)^2,
\qquad \operatorname{ICC}(A,1)=
 \frac{MS_R-MS_E}{MS_R+MS_E+2(MS_C-MS_E)/n}. \tag{23}
$$

At least two rows and a nonzero denominator are required. These formulas describe
statistics computed in the archived diagnostic code; they do not assert new
500-location ICC/CCC results beyond the published aggregate records.

## Appendix D. Evidence and reporting boundaries

The [500-location validation report](validation500_2026-10-25.md) contains all
12 target results and matched raw-Flash comparisons. For the 4,860 numeric
reference items, the final continuous output had $H_{0.1}=63.60\%$,
MAE 0.0865, and $L_{0.3}=2.16\%$; one-decimal output had $H_{0.1}=84.61\%$,
MAE 0.0761, and $L_{0.3}=3.60\%$. These are observed validation results, not
success thresholds or exact classification accuracies. Rounding raises both the
within-0.1 and large-error proportions; it does not improve visual recognition.
The historical >70% continuous hit-rate aspiration was not achieved.

The [full-run record](full_scoring_2026-10-25.md) establishes 36,480 valid Flash
responses and 145,920 finite scores per precision for the remaining 12,160
locations. It does not provide reference-based full-dataset accuracy. A separate
post-freeze nearest-original-anchor sensitivity analysis does not replace the
frozen one-decimal delivery or its validation and would require separate reporting.
No inference-time reference matching, new model fitting, or Flash requests are
part of this methodology publication.

Original images, complete private PDF-derived rubric, coordinates, reference
rows, split memberships, feature arrays, fitted coefficients, and point-wise
outputs are excluded from the public repository. This publication gives the
mathematical method, exact hyperparameter/tree specification, and a checked
inference reference; it is not a self-contained public reproduction dataset.

### References and supporting records

1. Oquab et al. *DINOv2: Learning Robust Visual Features without Supervision*.
   [Paper](https://arxiv.org/abs/2304.07193).
2. scikit-learn. [Ridge estimator and weighted fitting](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html).
3. scikit-learn. [Epsilon support-vector regression](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html).
4. [Final frozen method and audit](scoring_frozen_2026-10-25.md).
5. [Exact frozen model configuration](../configs/scoring/flash_v2_dino_canonical_frozen.json).
6. [Prompt/model iteration archive](scoring_iterations_2026-10-23.md).
7. [500-point validation and coverage](validation500_2026-10-25.md).
8. [Full-batch completion](full_scoring_2026-10-25.md).
9. [A/B reference-matching diagnostic](ab_dimension_diagnostic_2026-10-25.md).
10. [Read-only formula implementation](../scripts/scoring_frozen_reference.py).
