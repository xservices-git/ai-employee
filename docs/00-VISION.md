# Vision

## Muc tieu

**AI Employee la 1 orchestrator local** giup ban:
1. **Ghi nho** task da lam, context du an, ky nang da hoc
2. **Tu sua sai** (loai nho - sai kien thuc, khong phai bug code)
3. **Tu hoc** tu feedback (propose rules, HUMAN approve)
4. **Mo rong** cho nhieu domain qua file YAML

## Pham vi thuc te (KHONG marketing)

### Co the lam (100%)
- **Memory 3 tang**:
  - Episodic: SQLite task history (input, output, feedback)
  - Semantic: ChromaDB embeddings (tim task tuong tu, context)
  - Procedural: YAML rules (trigger + action + success_rate)
- **Feedback loop**: user cham 1-5 sao, sua output, comment
- **Rule extraction** (HUMAN GATE): AI propose rules, ban approve

### Co the lam mot phan (40%)
- **Tu sua sai loai nho** (sai kien thuc, dung sai tool): co the retry voi feedback
- **Pattern detection**: weekly cron tim rule moi tu 50+ feedback

### KHONG the lam hoac khong nen
- ❌ **Tu sua bug code production** - can nguoi fix
- ❌ **Auto-promote rules** - can human approve (an toan)
- ❌ **Fine-tuning pipeline** - can GPU A100, khong co tren laptop
- ❌ **Multi-agent 5 roles** - overkill, 1 orchestrator du
- ❌ **K8s + DR RTO 30p** - Docker Compose du cho SME
- ❌ **Helm chart** - khong can
- ❌ **100% self-improving** - 30% tu dong, 70% co human gate

## 7 task types (pham vi M1)

| ID | Ten | Mo ta |
|---|---|---|
| data_processing | Xu ly du lieu | Query/insert/update/delete DB |
| content_generation | Tao noi dung | Viet email, bao cao, bai viet |
| classification_routing | Phan loai | Phan loai ticket, email, don hang |
| monitoring_alerting | Giam sat | Check health, alert khi co van de |
| research_summarization | Nghien cuu | Search web, tom tat tai lieu |
| scheduling_coordination | Lich | Tao event, reminder, cron |
| decision_support | Ho tro quyet dinh | Phan tich, goi y, so sanh |

## Do luong thanh cong (KPIs)

- **Task success rate >= 80%** tren golden set (khong phai 90% - thuc te kho)
- **Auto-approval rate >= 60%** (40% can hoi nguoi)
- **P95 latency < 15s** voi 8B model local (khong phai 8s - 8B local cham)
- **Memory retrieval P95 < 200ms**
- **Hallucination rate < 5%** (Critic + fact-check)
- **100% local** - khong gui data ra ngoai

## KHONG phai muc tieu

- ❌ Thay the con nguoi 100% → **Tang cuong** nang luc nguoi dung
- ❌ Lam moi thu → **Lam tot 7 task types** da dinh nghia
- ❌ Multi-language real-time → **Tieng Viet + Anh** tot, khac la bonus
- ❌ Thay the ERP/CRM → **Tich hop** voi he thong co san

## Doi tuong

1. **SME** muon tu dong hoa ma data phai local
2. **Ops team** dang ngap trong email, ticket, don hang thu cong
3. **Developer** muon build AI agent khong phu thuoc OpenAI API
4. **Ca nhan** muon co "tro ly ao" hieu minh qua feedback

## Timeline thuc te (3 milestone)

| Milestone | Thoi gian | San pham |
|---|---|---|
| **M1** | 1-2 thang | Foundation: FastAPI + 1 orchestrator + SQLite + ChromaDB + 3 task types |
| **M2** | 2-3 thang | Feedback loop: 7 task types, rule propose (HUMAN), 100 eval cases |
| **M3** | 3-4 thang | Production: multi-user, monitoring, backup, 3 domains production |

**Tong: 6-9 thang**, khong phai 10-12 tuan (spec cu qua ao tuong).

## So voi spec cu (V3.0)

| Kha canh | Spec cu (V3.0) | Spec moi |
|---|---|---|
| Agents | 5 (Planner, Executor, Critic, Memory Curator, Supervisor) | 1 orchestrator |
| Memory | 3 tang + procedural tu promote | 3 tang + HUMAN approve |
| Learning | Auto self-improving | Propose + human gate |
| Deploy | K8s + DR + Helm | Docker Compose |
| Timeline | 6 giai doan 10-12 tuan | 3 milestone 6-9 thang |
| Code | 95 files push | Skeleton M1 (target) |
