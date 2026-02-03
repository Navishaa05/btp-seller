

================================================================================
DETAILED PHASE 2 BREAKDOWN: Machine Learning for CTR/CVR Prediction
================================================================================

### UNDERSTANDING THE PROBLEM

Current System (src/auction_sim/simulation/engine.py, line ~65):
   - Uses simple sigmoid-based prediction: CTR = sigmoid(user·ad) × base_ctr
   - Problem: Only uses user-ad similarity!
   - Missing: Time of day, historical performance, ad quality, context

Goal: Build ML models that predict:
   1. CTR (Click-Through Rate): P(user clicks ad)
   2. CVR (Conversion Rate): P(user converts | clicked)

---

### PART 1: FEATURE ENGINEERING (What Features to Extract)

Feature Categories (51 total features): 39 main features and 12 count feautres 

ques : currently user have no persistent id ? so shall i add a hash based 

1. USER EMBEDDING (16 features)
   - Raw user representation: [f1, f2, ..., f16]
   - Captures: interests, demographics, browsing history

2. AD EMBEDDING (16 features)
   - Raw ad representation: [f17, f18, ..., f32]
   - Captures: product category, price, seller info

3. INTERACTION FEATURES (3 features)
   - f33: Dot product (relevance score = user·ad)
   - f34: Cosine similarity (normalized relevance)
   - f35: Euclidean distance (dissimilarity)

4. TEMPORAL FEATURES (4 features)
   - f36: Hour of day (normalized 0-1)
   - f37: sin(2π × hour/24) - captures cyclical patterns
   - f38: cos(2π × hour/24) - captures cyclical patterns
   - f39: Is weekend? (0 or 1)

5. COUNT-BASED FEATURES (12 features) - THE SECRET SAUCE!
   User-level:
   - f40: total_impressions (how many ads user has seen)
   - f41: total_clicks (how many times user clicked)
   - f42: total_conversions (how many times user converted)
   - f43: user_ctr (clicks / impressions)
   - f44: user_cvr (conversions / clicks)
   
   Ad-level:
   - f45: total_impressions (how many times ad was shown)
   - f46: total_clicks (how many times ad was clicked)
   - f47: total_conversions (how many times ad converted)
   - f48: ad_ctr (clicks / impressions)
   - f49: ad_cvr (conversions / clicks)
   
   User-Ad pair:
   - f50: pair_impressions (how many times THIS user saw THIS ad)
   - f51: pair_clicks (how many times THIS user clicked THIS ad)

Implementation Files:
   - src/auction_sim/utils/features.py → extract_ctr_features()
   - src/auction_sim/data/feature_store.py → FeatureStore class

---

### PART 2: XGBOOST (Tree-Based ML Model)

What is XGBoost?
   - eXtreme Gradient Boosting
   - Builds many decision trees that correct each other's mistakes
   - Final prediction = weighted vote of all trees
   - NO HEAVY MATH NEEDED - it's a black box!

Why XGBoost for CTR/CVR?
   ✅ Handles non-linear relationships (e.g., CTR peaks at certain hours)
   ✅ Automatically finds feature interactions
   ✅ Robust to outliers
   ✅ Fast training (millions of samples)
   ✅ Feature importance analysis

Hyperparameters (start with these):
   - max_depth: 6 (tree depth)
   - learning_rate: 0.1 (step size)
   - n_estimators: 100-200 (number of trees)
   - objective: 'binary:logistic' (for CTR/CVR prediction)
   - eval_metric: 'auc' (Area Under ROC Curve)
   - scale_pos_weight: ~39 (handle class imbalance for CTR ~2.5%)

Installation:
   pip install xgboost scikit-learn pandas

---

### PART 3: IMPLEMENTATION PIPELINE

Week 1: Feature Engineering & Data Generation
   Day 1: 
   - Create src/auction_sim/utils/features.py
   - Implement extract_ctr_features(user_embed, ad_embed, context, history)
   - Test on one auction
   
   Day 2-3:
   - Create src/auction_sim/data/feature_store.py
   - Implement FeatureStore class with methods:
     * update(user_id, ad_id, impression, click, conversion)
     * get_user_stats(user_id)
     * get_ad_stats(ad_id)
     * get_pair_stats(user_id, ad_id)
   - Test update and retrieval
   
   Day 4-5:
   - Create src/auction_sim/data/generate_training_data.py
   - Run simulation to collect 100,000 samples
   - Output: data/training_data.parquet (100K rows × 53 cols)
   - Verify: CTR ~2-3%, CVR ~0.2-0.5%

Week 2: Model Training
   Day 1-2:
   - Create src/auction_sim/models/train_ctr_model.py
   - Train XGBoost classifier on CTR prediction
   - Target metrics: AUC > 0.75, Log Loss < 0.15
   - Save to: models/ctr_model.json
   
   Day 3-4:
   - Create src/auction_sim/models/train_cvr_model.py
   - Train on clicked samples only (CVR = P(convert | click))
   - Target metrics: AUC > 0.65 (CVR is harder!)
   - Save to: models/cvr_model.json
   
   Day 5:
   - Modify src/auction_sim/simulation/engine.py
   - Add use_xgboost parameter to simulate_block()
   - Replace sigmoid predictions with XGBoost.predict_proba()
   - Test with 1000 auctions

Week 3: Evaluation & Comparison
   Day 1-2:
   - Create scripts/compare_models.py
   - Run experiments: Sigmoid (baseline) vs XGBoost
   - Measure: Revenue lift, CTR accuracy, ROAS improvement
   - Expected: 10-20% revenue improvement
   
   Day 3-5:
   - Hyperparameter tuning (grid search)
   - Try: max_depth [3,6,9], learning_rate [0.05, 0.1, 0.2]
   - Cross-validation for robustness
   - Document best configuration

---

### PART 4: KEY CODE SNIPPETS

Feature Extraction Example:
```python
features = extract_ctr_features(user_embed, ad_embed, context, history)
# Returns: numpy array of 51 features
# Example: [0.5, -0.3, ..., 0.05, 3, 1] (embeddings + stats)
```

XGBoost Training Example:
```python
import xgboost as xgb
ctr_model = xgb.XGBClassifier(max_depth=6, learning_rate=0.1, n_estimators=200)
ctr_model.fit(X_train, y_train, eval_set=[(X_test, y_test)])
ctr_predictions = ctr_model.predict_proba(X_test)[:, 1]  # Probability of click
```

Integration Example:
```python
# In engine.py simulate_block()
if use_xgboost:
    features = extract_ctr_features(user_embed, ad_embed, context, FEATURE_STORE)
    CTR[t, s_idx] = CTR_MODEL.predict_proba(features.reshape(1, -1))[0, 1]
else:
    CTR = sigmoid(user @ ad.T) * base_ctr  # Old way
```

---

### REFERENCES & RESOURCES

Papers:
   1. "Ad Click Prediction: A View from the Trenches" (Google, 2013)
      - https://research.google/pubs/pub41159/
      - Count-based features, online learning
   
   2. "Practical Lessons from Predicting Clicks on Ads at Facebook" (2014)
      - https://research.facebook.com/publications/practical-lessons-from-predicting-clicks-on-ads-at-facebook/
      - Feature engineering, gradient boosted decision trees
   
   3. "Deep Learning for Click-Through Rate Estimation" (2017)
      - https://arxiv.org/abs/1708.05027
      - Wide & Deep models (future work)

Tutorials:
   - XGBoost Documentation: https://xgboost.readthedocs.io/
   - Scikit-learn Metrics: https://scikit-learn.org/stable/modules/model_evaluation.html
   - Imbalanced Classification: https://machinelearningmastery.com/xgboost-for-imbalanced-classification/
   - Count based feature misha bilenko -https://www.slideshare.net/slideshow/learning-with-counts/253345953 

Misha Bilenko's Work (Microsoft):
   - Search for: "count based features misha bilenko bing ads"
   - Key insight: Historical counts (user clicks, ad impressions) are powerful predictors
   - Implement: User-level, Ad-level, User-Ad pair statistics

---

### EVALUATION METRICS

CTR/CVR Model Quality:
   - AUC (Area Under ROC): 0.5 = random, 1.0 = perfect, target > 0.75
   - Log Loss: Lower is better, measures calibration
   - Calibration plots: Predicted CTR vs observed CTR

Business Impact:
   - Revenue lift: (XGBoost revenue / Sigmoid revenue - 1) × 100%
   - CTR improvement: Better predictions → better allocation
   - ROAS (Return on Ad Spend): Advertiser profitability

Feature Importance:
   - Which features matter most? (XGBoost provides importance scores)
   - Expected top features: user_ctr, ad_ctr, relevance_score, pair_clicks

---

### QUESTIONS TO ASK ADVISOR

1. Data Generation:
   - Should I use simulated data or is there real auction data available?
   - How many samples needed? (100K, 1M, 10M?)
   - Train on sigmoid labels or need ground truth?

2. Model Evaluation:
   - What's the baseline performance to beat? (current sigmoid AUC?)
   - Target metrics: AUC > X, Revenue lift > Y%?
   - Business metrics or just ML metrics?

3. Feature Store:
   - Real-time updates during simulation or batch compute?
   - How to handle cold-start? (new users/ads with no history)

4. Next Steps:
   - After XGBoost works, proceed to RL (Phase 3)?
   - Should I document comparison results for paper/report?

---

### NOTES & LEARNINGS

✅ Completed Understanding:
   - Feature engineering: 51 features across 5 categories
   - XGBoost: learnt 
   <!-- - Count-based features: Historical stats improve predictions -->
   - Pipeline: Generate data → Train → Evaluate → Integrate

⚠️ Challenges Expected:
   - Class imbalance: CTR ~2-3% (use scale_pos_weight)
   - Cold-start: New users/ads have no history (use other features)
   - Overfitting: Monitor train vs test AUC gap
   - Integration: Feature extraction must be fast (vectorize)

---



QUESTION: Is this Phase 2 plan correct? Should I proceed with implementation?


