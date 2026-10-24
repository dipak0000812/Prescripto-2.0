\# ML pilot results (research/demo mode, uncalibrated)



Pilot: 13 hand-labeled images, 57 labeled drugs. Images hand-picked, one labeler,

unlabeled real drugs count as errors. Drug-name recall only; strength/dose/frequency NOT yet evaluated.



| Approach | Drugs found | Note |

|---|---|---|

| Khedim fine-tuned TrOCR | not scored | produced fabricated text unrelated to the crop |

| TrOCR-base on Paddle line crops | 1/57 = 2% | rejected |

| Paddle + Qwen2.5 text structuring | 17/57 = 30% | precision 53% |

| Qwen2.5-VL 7B, whole image | 27/57 = 47% | precision 46% |

| Qwen2.5-VL + 3 strips | 28/57 = 49% | precision 35%, rejected |

| Final merge (Paddle + VLM) | 30/57 = 53% | 74% correct where both readers agree, \~20% otherwise |



Fuzzy match threshold 80. Reader agreement is a review-priority hint, not calibrated confidence.

All output is review\_required. Vocabulary is RxHandBD only (1,462 names), too small for Indian brands.



Pipeline: PaddleOCR (detect/recognize) + Qwen2.5-VL (reads image) + Qwen2.5 text structuring,

all local via Ollama; merge -> ml/extraction/to\_api\_rows.py -> prescription\_medications row shape.

