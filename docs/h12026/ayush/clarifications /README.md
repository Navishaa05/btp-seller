### Anil Notes 13Jan:

1. Ayush, consider starting with something simple like https://github.com/thaychansy/click-through-rate-prediction
2. Until user simulation is ready you will not know what user features are available. Until setup your training/inference pipelines and train them on some public data like this https://www.kaggle.com/datasets/gauravduttakiit/clickthrough-rate-prediction
3. You can then move to integrating auctiongym and come back to this a bit later to refine it. Count-based features can a bit tricky to setup though very simple and need ample data, get to it in the end.


# DOUBT DOC


1. Sir please review my Phase 2 plan(docs/h12026/ayush/LOGS/12JAN.md) for replacing the sigmoid model with XGBoost for bid price prediction in the auction module and tell me if this is the correct approach to proceed with implementation.

### QUESTIONS TO ASK ADVISOR

1. Data Generation:

    How to get / generrate datasets.
   - Should I use simulated data or is there real auction data available?
   - How many samples needed? (100K, 1M? HOW MUCH?)
   - Train on sigmoid labels or need ground truth?

2. Model Evaluation:
   - What's the baseline performance to beat? (current sigmoid AUC?)
   - Target metrics: AUC > X, Revenue lift > Y%?

3. Feature Store:
    - Are the 51 features ok ? about the count-based features , i googled "count based features misha bilenko" , found some lectures
    https://www.slideshare.net/slideshow/learning-with-counts/253345953
     didnt understnad much and didnt find any other thing , 
     So i did make some count based features by myself , please look into it , 

   - Real-time updates during simulation or batch compute?
   - How to handle cold-start? (new users/ads with no history)

4. Next Steps:
   - After XGBoost works, proceed to RL (Phase 3)?
   - Should I document comparison results for paper/report?
