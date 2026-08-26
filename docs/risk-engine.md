# AeroMind ClimateGuard — Deterministic Risk Engine Specification

## 1. Core Principle
The AeroMind Risk Engine is strictly **deterministic**, **mathematical**, and **explainable**. Numerical scores are calculated exclusively by compiled deterministic logic, never by an LLM.

---

## 2. Risk Score Formulation

The composite risk score $R \in [0.0, 100.0]$ is computed as the bounded linear combination of normalized factors:

$$R = \min\left(100.0, \; \sum_{i} w_i \cdot F_i\right)$$

### Contributing Factors ($F_i$):

1. **Temperature Elevation Factor ($F_{\text{temp}}$)**:
   $$F_{\text{temp}} = \min(25.0, \; 1.8 \cdot \max(0, T_{\text{current}} - T_{\text{baseline}}))$$

2. **Statistical Anomaly Factor ($F_{\text{anomaly}}$)**:
   $$F_{\text{anomaly}} = \min(20.0, \; 20.0 \cdot S_{\text{anomaly}})$$

3. **Thermal Rate of Change Factor ($F_{\text{RoC}}$)**:
   $$F_{\text{RoC}} = \begin{cases} 0 & \text{if } \text{RoC} \le 1.5^\circ\text{C/hr} \\ \min(15.0, \; 4.0 \cdot (\text{RoC} - 1.5)) & \text{if } \text{RoC} > 1.5^\circ\text{C/hr} \end{cases}$$

4. **Visual Computer Vision Hazards ($F_{\text{visual}}$)**:
   - **Active Fire / Flame**: $+35.0 \times \text{Confidence}$
   - **Optical Smoke Plume**: $+25.0 \times \text{Confidence}$
   - **Equipment Thermal Hotspot**: $+18.0 \times \text{Confidence}$

5. **Human Danger Zone Proximity ($F_{\text{proximity}}$)**:
   $$F_{\text{proximity}} = \min(20.0, \; 10.0 + 5.0 \cdot N_{\text{danger\_people}})$$

6. **Condition Persistence Factor ($F_{\text{persistence}}$)**:
   $$F_{\text{persistence}} = \min\left(10.0, \; \frac{t_{\text{unmitigated\_minutes}}}{30.0} \times 10.0\right)$$

---

## 3. Severity Classification Scale

| Score Range | Severity Level | Operational Protocol Directive |
| :--- | :--- | :--- |
| **0 – 29** | **LOW** | Nominal background operations; baseline polling |
| **30 – 59** | **MEDIUM** | Enhanced sensor polling; notify sector supervisor |
| **60 – 79** | **HIGH** | Urgent on-site inspection; dispatch containment team |
| **80 – 100** | **CRITICAL** | Automated fire suppression; sector emergency evacuation |

---

## 4. Transparent Factor Attribution Example

```
Overall Risk Score: 87.0 (CRITICAL)
- Temperature Elevation: +18.5 (+10.3°C above baseline)
- Rapid Thermal Rate of Change: +14.8 (Rising at 5.2°C/hr)
- Visual Fire Confirmation: +33.2 (Optical confirmation with 95% confidence)
- Human Presence in Risk Zone: +15.0 (1 personnel tracked in high-risk perimeter)
- Condition Persistence: +5.5 (Condition unmitigated for 16 minutes)
```
