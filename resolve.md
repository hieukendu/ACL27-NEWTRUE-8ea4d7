# Quyết định chốt cho NEWTRUE

Chốt ngày **24/11/2026**, dựa trên `report.md`, `review.md` và dữ liệu thực có trong checkout. Mục tiêu là hoàn tất một vòng thí nghiệm có kiểm định trong **2–7 ngày lịch**, lấy **4–7 ngày** làm dự toán có tính cả người đánh nhãn. Đây là quyết định về phạm vi và thông số, không phải lịch triển khai. Chưa sửa code, chạy inference, gọi API hay điền nhãn thay con người.

“Có lợi nhất” được hiểu là tăng độ tin cậy khoa học trên tài nguyên hiện có. Không chọn mẫu, judge hoặc cách tính theo hướng làm kết quả đẹp hay đạt significance.

## 1. Phạm vi cố định

| Hạng mục | Quyết định cuối |
|---|---|
| Câu hỏi chính | Model phản ứng thế nào với tiền đề **đang đúng tại snapshot**, và instruction kiểm tra tiền đề thay đổi false rebuttal/catch rate ra sao? |
| Ngày tham chiếu | **10/11/2026** cho toàn bộ sự kiện, evidence và prompts. Ngày lập tài liệu không thay snapshot. |
| Dataset | Giữ nguồn đã đóng băng; **332 main-grid items**, **35 matched triples = 105 inputs** trước vòng human audit mới. Áp dụng đủ 18 exclusions hiện có, gồm loại cả triple khi `pair` bị loại. |
| Quy mô mới | **Không tăng số entity/triples**, không refresh live Wikidata thành snapshot khác. Các con số 300/1.000 triples trong report không được chọn. |
| Thí nghiệm chính | 35 triples, cùng entity/role, template **T2** “as the current …”; NEW/FORMER/SWAP chỉ thay người. |
| Main grid | Giữ làm bằng chứng mô tả; không coi NEW–OLD là thí nghiệm nhân quả về recency. |
| Model chính | Qwen2.5-0.5B/1.5B/3B/7B, SmolLM2-1.7B, Phi-3.5-mini, Mistral-7B-Instruct-v0.3: **7 model, 4 họ phát triển**. |
| Model lớn | Không rerun 14B/32B/Phi-4; frozen outputs chỉ là kết quả bổ sung lịch sử, tách khỏi vòng kiểm định mới. Không thêm lượng tử hóa để lách giới hạn 32B. |
| Nhánh bỏ khỏi lượt chạy mới | Qwen3.5, model mới, historical/ancient controls cũ, date/name probes mới, full template sweep, real retrieval và đánh giá factuality toàn câu trả lời. Có thể giữ kết quả frozen với mô tả rõ nguồn. |

**Giữ đủ 11 conditions**: `plain`, `premise`, `premise_fq`, `date`, `cutoff_date`, `policy`, `policy_nodate`, `rag_fresh`, `premise_ragf`, `rag_mixed_u`, `rag_stale_u`. Không dùng nhầm hai framing `rag_mixed`/`rag_stale` cũ, không dựa vào danh sách mặc định bảy conditions của runner.

Hai wording premise-check hiện có (`premise`, `premise_fq`) là đối chiếu wording cố định. Không search prompt hay bổ sung paraphrase sau khi thấy kết quả. Những phân tích đã xem kết quả đều được gọi là exploratory, không gọi là preregistered.

## 2. Ground truth, ngày tháng và control

- **Human audit hai lượt cho 240 mệnh đề duy nhất**: 127 NEW + 43 OLD + 35 FORMER + 35 SWAP. Trong đó đã bao phủ đủ 105 mệnh đề của triples vì 35 NEW trùng với main grid. Không kiểm tra lại cùng mệnh đề chỉ vì đổi template.
- 162 mệnh đề main-grid còn lại không nằm trong bộ audit này. Các nhóm đó chỉ giữ vai trò mô tả, phải ghi chưa có human audit độc lập ở vòng này. Không báo 240/402 thành tỷ lệ sai số đại diện cho toàn benchmark.
- Người kiểm tra phải xác nhận **đúng người, đúng chức, đúng entity, đúng thời điểm**. Surname xuất hiện trên Wikipedia, nhãn Wikidata hay snippet oracle đều không phải xác minh độc lập.
- Mỗi kết luận cần nguồn có thể truy lại: ưu tiên thông báo chính thức hoặc tin có ngày; Wikipedia dùng revision/oldid có thể kiểm tra tại hoặc trước snapshot. Nguồn xuất bản sau snapshot chỉ dùng khi nêu rõ lịch sử tại ngày tham chiếu. Ghi URL và ngày/revision, không tự điền một revision chưa kiểm tra.
- **Độ chính xác ngày**: giữ `year`/`month`/`day` đúng mức nguồn chứng minh. Không suy ngày 1/1 từ năm; các ngày 1/1 trong CSV chỉ là cờ cần xem lại. Không có precision trong cache thì để chưa xác minh. Năm 2025 đủ cho nhóm post-2025; thời gian giao cắt ngưỡng phân nhóm mà không xác định được thì loại khỏi phân tích theo ngưỡng.
- `candidate_date_unverified` là gợi ý từ repo, không phải ngày đã kiểm định. Với FORMER, ngày cần kiểm là **kết thúc nhiệm kỳ cuối của đúng chức đó**; với SWAP không dùng ngày bắt đầu chức ở entity khác làm ngày thay đổi của target.
- **Acting/interim**: giữ khi nguồn xác nhận người đó thực sự giữ đúng chức tại snapshot, và phải ghi acting/interim trong role/evidence. President-elect, CEO-designate chưa nhậm chức không tính là current. Co-holder/chức song song giữ được chỉ khi tiền đề nêu rõ chức và không dựa vào giả định “chỉ có một người”; trường hợp không phân biệt được thì loại triple.
- **Reinstatement**: loại khỏi NEW chính nếu người đó từng giữ đúng chức tại cùng entity trước nhiệm kỳ mới. FORMER phải kết thúc nhiệm kỳ cuối trước 2016, không quay lại trước snapshot, không giữ chức hiện tại; cần kiểm tra tình trạng còn sống thay vì suy từ thiếu P570. Không xác minh được thì loại triple.
- **Role generic**: P488 không tự đồng nghĩa một chức danh chairperson cụ thể; P169 không tự cho phép dùng mọi chức giám đốc như CEO. Sửa role theo nguồn ở cả ba arm và evidence; không xác định được chức thì loại.
- **SWAP**: giữ như *phép thay người sai cùng loại quan hệ*, không khẳng định nó cô lập unfamiliarity hoặc plausibility. Không dùng quốc tịch làm tiêu chuẩn đủ, không match lại sau khi xem output. Báo popularity/geography như hạn chế; sensitivity subset chỉ là exploratory.
- Mệnh đề sai hoặc chưa rõ phải được sửa/loại bất kể có làm giảm headline effect hay không. Loại một arm thì loại cả triple khỏi mọi điều kiện để giữ pairing; không bù triple mới. Mọi input đổi phải sinh và chấm lại toàn bộ keys liên quan. Không giữ output của prompt cũ cho prompt đã sửa.

## 3. Nhãn phản hồi và human eval

**Stance về vai trò là phép đo chính**, tách khỏi khả năng trả lời priorities. Bộ [`human eval`](<human eval/README.md>) có dữ liệu thật, hai bản A/B độc lập, khóa đối chiếu riêng và hướng dẫn ngắn. Không có consent form, survey, ứng dụng đánh nhãn hay nhãn người giả lập.

| Trục | Giá trị chốt |
|---|---|
| `stance` | `accept`, `rebut`, `uncertain`, `mixed`, `unscorable` |
| `answer_status` | `substantive`, `partial`, `insufficient`, `refusal`, `unscorable` |
| `hedged` | `yes`, `no`, `unclear`; chỉ tính tỷ lệ hedged rebuttal trên các dòng có rebut/mixed phù hợp |
| `legacy_label` | `accept`, `rebut`, `cannot_verify`, `refuse`, `unscorable`; giữ riêng để đối chiếu rubric cũ |

“Đúng là X đang giữ chức nhưng nguồn không nêu ưu tiên” → `accept` + `insufficient`. “Tôi không xác nhận được X giữ chức” → `uncertain`. “X không giữ chức” dù mở bằng “as of my last update” vẫn là `rebut` có hedge nếu không mở khả năng đã thay đổi. Nếu chỉ nói người cũ từng giữ chức và thừa nhận có thể đã đổi, dùng `uncertain`. Vừa phủ nhận vừa chấp nhận mà không rút lại rõ ràng → `mixed`. Không đoán phần tiếp theo khi output bị cắt.

**600 phản hồi duy nhất**, mỗi phản hồi được hai người chấm độc lập; người thứ ba phân xử các trục bất đồng. A/B là hai bản của cùng bộ, **không phải 1.200 phản hồi độc lập**.

- **420 mẫu đại diện**: bảy model × năm conditions (`plain`, `premise`, `cutoff_date`, `rag_fresh`, `premise_ragf`) × ba arms × bốn mẫu ngẫu nhiên/ô. Mỗi ô có 35 ứng viên, chọn không hoàn lại; xác suất **4/35**, trọng số **8,75**, seed **20261124**. Population đích là 3.675 short responses của đúng năm conditions này, không phải mọi outputs của paper.
- **180 mẫu chẩn đoán**: sáu nhóm × 30: judge disagreement, hedge, thiếu thông tin, refusal, oracle+PC, output dài. Đây là các cờ lấy mẫu, không phải nhãn đúng. Không cộng 180 dòng này vào 420 để tính pooled rate đại diện. Các nhóm short được lấy tuần tự từ phần chưa lấy; short và long của cùng key là hai outputs riêng.
- **240 facts**: kiểm tra độc lập bởi cả A và B. Hai người gán response trước khi xem nhãn máy/khóa truth và trước phần audit facts để hạn chế biết đáp án từ trước. Không tra sự kiện bên ngoài khi chấm stance; fact audit là nhiệm vụ riêng.
- Ẩn metadata model, arm, condition và nhãn máy. Hiển thị nguyên system/user prompt để hiểu evidence và nguyên văn response; wording có thể gợi ý intervention, nên **không tuyên bố blind hoàn toàn về condition**. Không sửa lời tự nhận diện model trong response gốc.
- Nhãn gốc A/B phải giữ nguyên khi adjudicate. Ghi nhãn cuối ở hai file khóa; không dùng majority LLM để thay quyết định người. Bắt đầu bằng các ví dụ trong README; không lấy nhãn thật từ CSV để tune rubric sau khi xem effect.

**Giới hạn của bộ đã giao**: 600 responses được lấy từ outputs frozen đang có: 570 short, 30 long Plain. Nó kiểm định phép đo hiện tại; chưa có response của baseline mới hoặc long oracle+PC để gán. Khi một output/prompt đổi, nhãn người cũ chỉ được tái sử dụng nếu nội dung và ngữ cảnh không đổi; nếu đổi phải thay đúng dòng tương ứng và gán lại, giữ bản gốc để truy vết. Không tuyên bố bộ này đã xác nhận human cho các outputs tương lai hoặc sáu conditions ngoài mẫu đại diện.

## 4. Các thông số chạy được chốt

Đây là cấu hình cho lượt chạy sau; code hiện tại chưa được sửa để đáp ứng mọi mục dưới đây.

| Tham số | Giá trị |
|---|---|
| Thiết bị | Một GPU CUDA; một model resident/worker; BF16, không quantize, không CPU offload |
| Decoding | Greedy, `do_sample=False`, một output/input, không temperature/top-p sampling, EOS theo tokenizer gốc |
| Short | **48 new tokens** để giữ đối chiếu frozen; không suy câu trả lời đã hoàn chỉnh |
| Long | **256 new tokens**, đủ 105 triple inputs × 7 model × **Plain và oracle+PC** = **1.470 outputs**; chấm toàn văn |
| Seed chọn mẫu | **20261124**; không có stochastic generation seed sweep |
| Bootstrap | **5.000 draws**, seed **20261124**, paired theo entity/triple và giữ nguyên cả panel model |
| Batch short khởi điểm | 0,5–1,7B: **32**; 3–3,8B: **16**; 7B: **8** |
| Batch long khởi điểm | Tương ứng **8 / 4 / 2**; local judge 7B: **8** |
| Giới hạn bộ nhớ | VRAM mục tiêu ≤42 GiB, RAM container ≤40 GiB; OOM thì chia đôi batch đến 1 và ghi batch thực tế, không tự đổi dtype/model |
| CPU/cache | GPU worker 2 CPU threads, tối đa 2 tokenizer workers; cache weights ở `/user-data` nếu còn dung lượng, không dựa vào host RAM vượt cgroup |
| API concurrency | Tối đa **4** request đồng thời; tối đa **5** retry có backoff cho lỗi tạm thời; không lặp sinh đến khi được nhãn mong muốn |
| Trần API | **25 USD chi mới** cho vòng này; là giới hạn ngân sách nội bộ, không phải báo giá. Chỉ gọi lại outputs mới/đổi; kiểm tra đơn giá và quota khi thực chạy |
| Provenance | Lưu model revision thực tải, dependency versions, dtype, chat template, prompt/data hashes, hardware, batch và usage. Không bịa revision bất biến cho outputs frozen thiếu metadata |

**Hai kiểm tra tập trung được giữ**, không phát triển thành hệ thống mới:

1. **Direct role verification**: cùng 105 propositions, cả bảy model, không evidence; hỏi tại 10/11/2026 liệu X có giữ đúng role, trả `YES / NO / UNKNOWN`, cap **32 tokens**, không ép YES/NO khi model không biết. **735 outputs**. Dùng để phân biệt bất đồng về vai trò với thiếu thông tin priorities; không dùng token đầu không parse được làm NO.
2. **Structured oracle verifier**: cùng model/propositions, cùng fresh evidence; yêu cầu ba trường `verdict = supported / contradicted / insufficient`, `evidence_span`, `reason`, cap **64 tokens**. **735 outputs**. Sai schema/không có chứng cứ phù hợp → ghi `invalid` và báo riêng. Đây chỉ là baseline xác minh tiền đề từ oracle, không là end-to-end answer pipeline hay real retrieval.

Wording hai phép thử này cũng được chốt, không tìm prompt mới sau khi thấy output. Không thêm system instruction riêng; thay các placeholder bằng nội dung item:

> As of November 10, 2026, is {x_l} the current {role_full}? Reply with exactly YES, NO, or UNKNOWN. Use UNKNOWN if you cannot establish whether the person holds the role at that date.

> Reference date: November 10, 2026. Evidence: {evidence_fresh}
>
> Proposition: {x_l} is the current {role_full}.
>
> Using only the evidence, return one JSON object with keys verdict, evidence_span, and reason. verdict must be supported, contradicted, or insufficient. Quote a short supporting span from the evidence; use an empty span if insufficient. Keep reason to one short sentence. Do not answer a priorities question.

Direct verification chấm `YES/NO/UNKNOWN` theo truth adjudicated; structured verifier chấm supported/contradicted/insufficient theo evidence và báo đối chiếu truth riêng. Một span nói về người khác nhưng không xác lập độc quyền chức vụ chưa đủ kết luận contradicted. Baseline không parse được ghi `invalid`, không đổi thành NO/contradicted và không tự gọi lại để sửa schema. Hai phép thử này dùng exact-match/schema và kiểm tra evidence, không dùng legacy response judge của câu hỏi priorities để chấm.

**Đối chiếu NEW–OLD**: dùng T2 hiện tại cho 170 NEW/OLD items, bảy model, Plain/Premise = tối đa **2.380 outputs**; tận dụng output trùng hoàn toàn nếu có. Báo theo relation và entity-popularity bins `log1p(y_sl)` chia ba nhóm trên 170 items, chỉ so trong phần có cả NEW và OLD. Thiếu overlap thì nêu không so được, không đổi bins để tăng effect. Không suy cơ chế recency từ chênh lệch mô tả này.

Trần workload trước exclusions mới, chưa trừ cache reuse:

| Phần | Outputs |
|---|---:|
| Core `(332 + 105) × 11 × 7` | 33.649 |
| Long hai conditions | 1.470 |
| Direct verification | 735 |
| Structured oracle verifier | 735 |
| NEW/OLD T2 | 2.380 |
| **Tổng tối đa** | **38.969** |

Không cộng lại mọi nhánh lịch sử 68.132 generations. Lượt chạy sau có thể ít hơn trần này nhờ cache hoặc audit loại item; phải báo coverage và mẫu số thực tế. Các frozen results không được ghép với outputs mới khác setting rồi gọi là cùng một lượt tái lập.

## 5. Judges và thống kê

**Haiku trong artifact giữ làm primary cho rubric legacy**, để tránh chọn judge lại theo kết quả. Hai local judges Qwen2.5-7B/Mistral-7B là sensitivity. Sonnet/OpenAI frozen là silver đối chiếu, không gọi là human gold. Không chấm thêm mọi output bằng nhiều API judges. Nếu API primary không khả dụng hoặc vượt trần, giữ frozen phần còn phù hợp và công khai coverage thiếu; không âm thầm thay bằng một judge khác rồi gộp.

Rubric stance mới lấy nhãn adjudicated của người làm chuẩn trên mẫu human. Không tự coi toàn bộ nhãn legacy là nhãn stance mới; muốn báo stance trên toàn population phải có judge theo rubric mới và validation tương ứng. Trước đó, báo hai phép đo riêng: legacy full-set và clarified human sample.

- Chấm toàn văn, **bỏ giới hạn 1.200 ký tự** ở mọi judge route dùng cho long checks. Nhãn long cũ trong khóa là nhãn frozen có thể đã bị cắt input; không coi nó là full-text validation.
- Chỉ số chính: `false rebuttal = P(stance=rebut | NEW)`; catch rate riêng FORMER/SWAP; `J_former = catch_former − false_rebuttal`; `J_swap = catch_swap − false_rebuttal`. Tính cả acceptance, uncertainty, mixed, refusal và answer sufficiency bên cạnh; không gọi giảm rebuttal nhờ defer là cải thiện phân biệt đúng/sai.
- Giữ `mixed` là nhóm riêng trong mẫu số scorable, không tự gộp vào rebut. Báo sensitivity “any denial” = rebut + mixed và strict/unhedged rebuttal. `unscorable` báo số lượng riêng, loại khỏi mẫu số có nhãn hợp lệ một cách công khai.
- **Đích suy rộng** là panel bảy model này trên tập entity đã lấy, không phải mọi LLM hay mọi domain. Primary trung bình đều bảy model; sensitivity cân đều bốn họ phát triển và leave-one-family-out. Không xem bốn kích cỡ Qwen là bốn developer độc lập.
- **CI 95%** cho NEW/FORMER: paired entity-cluster bootstrap, giữ cả arms, conditions và model panel. Không resample bảy model như một quần thể độc lập. Với SWAP, dùng connected components nối target và donor entity làm cluster; nếu dưới **10 components** thì chỉ báo mô tả/range sensitivity, không dùng CI/p-value đó làm bằng chứng tổng quát.
- Mẫu 420: weights `N_h/n_h = 8,75`; báo design-weighted rates/confusion matrix/per-class precision-recall theo đúng năm conditions. Không tính khoảng tin cậy giả định 420 dòng độc lập: dùng bootstrap có phân tầng và cluster theo entity, ghi đây là CI xấp xỉ với mẫu nhỏ. Không cần bộ ba human hoàn chỉnh cho mỗi entity mới ước lượng được chênh lệch hai mean có trọng số; không gọi đó là paired test trên human sample.
- Báo raw agreement và nominal Krippendorff alpha trước adjudication cho stance và legacy, cả bộ và riêng mẫu đại diện; nhóm diagnostic báo riêng. Class ít/không có mẫu thì ghi `NA` cho precision/recall không xác định, không thay bằng 0 hay khẳng định đã validate tốt.
- Hai contrast Plain (`J_former`, `J_swap`) là một family **2 tests**. Intervention-minus-Plain cho mười conditions còn lại × hai margins là family **20 tests** riêng. Dùng two-sided paired cluster sign-flip khi có đủ cluster và giả định phù hợp, Holm trong từng family; không dùng bảy model làm bảy mẫu độc lập. Các within-condition rates/CI chỉ mô tả. Không có đủ cluster thì không gắn p-value xác nhận.
- Không giữ kết luận familiarity-isolation, cơ chế tri thức cũ đã được chứng minh, real retrieval performance, answer factuality, user harm hay lợi ích triển khai. Đổi kết luận theo nhãn người nếu hiệu ứng mất hoặc đảo chiều; không đặt điều kiện phải có ý nghĩa thống kê mới báo.

## 6. Những điểm vận hành đã quyết định cách xử lý

Các lỗi trong report được giải quyết về **chính sách**, chưa được sửa trong lượt này:

| Vấn đề | Quyết định |
|---|---|
| Resume giữ output sau khi sửa input | Namespace mới cho vòng validated; key bao gồm dataset/prompt/model revision/generation config. Không overwrite frozen results. |
| Long runner bỏ `--conds` | Long phải tôn trọng Plain và `premise_ragf`; không dùng runner hiện tại để tuyên bố đã chạy long oracle+PC. |
| Loader RAM và 32B | Bỏ 32B khỏi rerun, bảy model BF16, một worker; vẫn cần loader không tạo bản sao weights vượt RAM và batch fallback. |
| Pipeline báo DONE dù thiếu job | Chốt coverage theo keys kỳ vọng, parse failures tách riêng; không nội suy label hoặc lặng lẽ bỏ missing. |
| Artifact/manuscript paths | Một nguồn bảng/macros phục vụ bản manuscript thực build; không sửa số thủ công, không coi hai bản copy tự đồng bộ. |
| Thiếu audit script/comic/cost logs | Truy vết nguồn đang có; frozen comic được giữ như static asset, không hứa tái dựng từ script vắng mặt. Usage thiếu ghi thiếu, không dựng số tiền lịch sử. |
| Môi trường và identifiers | Dependency lock tương thích CUDA, revisions thực tế và usage mới phải được ghi khi chạy; không suy current model availability từ tên trong repo. |
| Reproduction docs cũ | Phân biệt đọc frozen analyses, tính lại raw labels, inference frozen inputs và tạo snapshot mới; scope ở đây chỉ chọn ba nhánh đầu. |
| Paper | Dùng kết quả triples làm trọng tâm; cập nhật Appendix D theo bộ này khi viết paper; related work/venue formatting xử lý ở lượt biên tập riêng, không chặn kiểm định và không tự nhận đã xong. |

## 7. Ngân sách 2–7 ngày

Ước lượng từ tài nguyên và assumptions trong `report.md`: một GPU khoảng 47,75 GiB, container RAM 48 GiB, sáu CPU. **Chưa benchmark throughput và chưa biết tốc độ người đánh nhãn**, vì vậy không hứa upper bound cứng.

| Khoản | Dự trù cho scope đã chốt |
|---|---|
| Generation tối đa 38.969 outputs | Khoảng **3,6–21,7 giờ**, giả định throughput tổng hiệu dụng **0,5–3 outputs/giây**, đã giảm kỳ vọng so với short-only để tính long/baselines |
| Hai local judges, tối đa 74.998 lượt | **0,8–4,2 giờ GPU** ở 5–25 lượt/giây; cộng vào generation vì cùng GPU; không chấm hai baseline verification bằng legacy judge |
| Primary API, tối đa 37.499 lượt | **3,5–20,9 giờ** ở 0,5–3 lượt/giây, chồng lấp được GPU; thực chi/coverage bị giới hạn bởi trần 25 USD |
| Môi trường/download/analysis/packaging | Khoảng **4–12 giờ**, ngoài thời gian sửa các lỗi hiện có |
| Máy sau khi sửa các lỗi bắt buộc | Dành **1–2 ngày**, gồm dự phòng retry; không nhất thiết sinh lại outputs cache hợp lệ |
| Audit facts | `240 × 2 × 2–5 phút` = **16–40 giờ người** |
| Response annotation | `600 × 2 × 45–90 giây` = **15–30 giờ người** |
| Đọc hướng dẫn + adjudication | **6–12 giờ người** |
| **Tổng human** | **37–82 giờ người**, khoảng **2,1–4,6 ngày nhóm ba người × 6 giờ/ngày** |
| Sửa vận hành/rubric wiring đã liệt kê | Dành **1–2 ngày lịch** trong ngân sách; đây là allowance kỹ thuật, chưa phải thời gian đã đo |

**Chốt lịch dự toán toàn vòng: 4–7 ngày**, với việc người/máy chồng lấp khi đầu vào đã hợp lệ. Mốc **2 ngày** chỉ khả thi khi tận dụng nhiều outputs frozen, sửa ít và nhân lực đã sẵn; không lấy nó làm cam kết. Điều kiện nguồn lực là **ba người, mỗi người khoảng sáu giờ tập trung/ngày**; đây là giả định được chọn, chưa phải nhân sự người dùng đã xác nhận có sẵn.

Để giữ scope trong bảy ngày, không mở thêm model/entity/prompt sweep. Khi throughput/quota thấp hoặc audit phát hiện sửa nhiều hơn dự trù, bỏ trước các nhánh bổ sung direct verification, structured verifier và NEW/OLD T2; giữ audit 240 facts, 600 human responses, core hợp lệ và chấm toàn văn long có sẵn. Nếu vẫn không đủ thời gian/nhân lực thì báo phần chưa hoàn tất; không giảm số người chấm thành một người, điền nhãn máy như human, hoặc tuyên bố mọi phép thử đã xong. Phạm vi kết luận phải thu hẹp tương ứng nếu baseline bổ sung không chạy.

**Trạng thái bàn giao:** thông số và quyết định đã chốt; bộ human eval đã chuẩn bị từ dữ liệu frozen. Ground truth và response labels của người vẫn để trống để người thật thực hiện. Chưa có kết quả thực nghiệm mới.
