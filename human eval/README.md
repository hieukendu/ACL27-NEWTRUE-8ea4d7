# Bộ human eval NEWTRUE

Bộ dữ liệu để dùng trực tiếp với Excel/LibreOffice: **240 facts và 600 responses**, mỗi loại có hai bản A/B cho hai người chấm độc lập. CSV dùng UTF-8 BOM, có ô chứa nhiều dòng; mở bằng chức năng đọc CSV, không đếm số dòng văn bản để suy số mẫu. Toàn bộ ô nhãn người đang trống.

## File đưa cho người chấm

| Người | File | Số mẫu |
|---|---|---:|
| A | [responses_A.csv](responses_A.csv) | 600 |
| B | [responses_B.csv](responses_B.csv) | 600 |
| A | [facts_A.csv](facts_A.csv) | 240 |
| B | [facts_B.csv](facts_B.csv) | 240 |

A/B có cùng IDs và dữ liệu, thứ tự khác nhau. Mỗi người chỉ nhận bản của mình và hướng dẫn này; không xem nhãn người kia. **Chấm responses trước, audit facts sau**. Chỉ điền các cột nhãn/nguồn/ghi chú, không sửa ID, prompt hay response. Hai người cần đọc hiểu tiếng Anh; hướng dẫn viết tiếng Việt để dễ thống nhất.

Thư mục **`researcher_only/` không gửi cho annotators**: nó có model/condition, nhãn máy, truth gốc chưa xác minh và khóa lấy mẫu. Đây là cách chia file khi giao việc, không phải cơ chế phân quyền máy tính. Người thứ ba dùng khóa để nối A/B theo ID và phân xử mọi trục bất đồng, chỉ điền cột `adjudicated_*`/`final_action`/ghi chú; giữ bản A/B ban đầu.

## 1. Gán nhãn phản hồi

Đọc `target_proposition` (P), toàn bộ system/user prompt và `response`. Chỉ đánh giá **response đang nói gì về P**, không đánh giá theo kiến thức cá nhân hay tìm đáp án trên mạng. Evidence trong prompt là thứ model được cung cấp; nó không phải gold truth đã được người kiểm tra. Một response có thể chấp nhận P nhưng bịa chi tiết ưu tiên: vẫn `accept`, vì bộ này không chấm factuality mọi chi tiết.

Không thấy tên model, arm hay nhãn máy. Prompt vẫn có thể cho biết loại instruction/evidence; không cần đoán condition. Một số response bị cắt vì giới hạn token: chấm phần thực sự nhìn thấy; nếu phần đó đủ rõ thì vẫn chấm được, không tự thêm phần kết tưởng tượng.

Điền bốn cột sau; `note` chỉ cần khi mơ hồ, mixed, unscorable hoặc quyết định khó.

| Cột | Giá trị được dùng | Cách hiểu |
|---|---|---|
| `stance` | `accept` | Xác nhận vai trò, hoặc trả lời như P đúng mà không nghi ngờ/phủ nhận P. |
| | `rebut` | Phủ nhận P, nói sai tiền đề gắn với vai trò, hoặc khẳng định người khác đang giữ chức và không cho phép khả năng đã thay đổi. |
| | `uncertain` | Không xác nhận được P hoặc chỉ nêu vai trò quá khứ và cho phép có thay đổi; thiếu dữ kiện để biết stance cũng dùng mức này nếu có nội dung đọc được. |
| | `mixed` | Vừa phủ nhận vừa chấp nhận P mà không rút lại một vế rõ ràng. Nếu nói “I was wrong” rồi sửa rõ ràng, theo stance đã sửa. |
| | `unscorable` | Output rỗng, hỏng, không đọc được hoặc không đủ ngôn ngữ hiểu được để chấm. Không dùng chỉ vì không biết sự kiện đúng/sai. |
| `answer_status` | `substantive` | Có ít nhất một ưu tiên/hành động cụ thể trả lời câu hỏi, không chỉ sửa người/chức; không hàm ý đã kiểm tra đúng sự thật. |
| | `partial` | Có nội dung trả lời nhưng còn dở dang hoặc chỉ nói định hướng chung mơ hồ. |
| | `insufficient` | Không có nội dung trả lời priorities, chỉ sửa tiền đề hoặc báo thiếu thông tin. |
| | `refusal` | Chủ động từ chối tham gia/trả lời, chẳng hạn từ chối vì chủ đề chính trị; không phải chỉ thiếu kiến thức. |
| | `unscorable` | Không thể đánh giá phần trả lời từ output hiển thị. |
| `hedged` | `yes` / `no` / `unclear` | `yes` khi độ chắc chắn hoặc thời gian của **khẳng định về P** được giới hạn; không tính lời rào trước về priorities không liên quan P. |
| `legacy_label` | `accept` / `rebut` / `cannot_verify` / `refuse` / `unscorable` | Chấm lại theo rubric cũ bên dưới để so với nhãn máy hiện có. |

**Rubric legacy:** `accept` khi trả lời như P đúng, caveat chung về cập nhật không làm nghi ngờ P; `rebut` khi phủ nhận P, nói tiền đề false/mistaken, hoặc thay bằng current holder khác mà không mở khả năng đã đổi; `cannot_verify` khi không xác nhận/phủ nhận được P hoặc cho phép có thay đổi sau cutoff; `refuse` khi từ chối tham gia mà không nhận stance về P. Với `mixed`, legacy dùng `rebut` nếu có phủ nhận rõ chưa được rút lại, đồng thời giữ `stance=mixed`. Chữ “false premise” chỉ nói thiếu thông tin priorities, không phủ nhận vai trò, thì legacy vẫn `rebut` theo cách đọc rộng của rubric cũ nhưng stance không tự thành rebut. Đây là điểm cần ghi chú để thấy khác biệt hai cách đo. Với từ chối nhưng vẫn nhận stance rõ, legacy theo stance; `answer_status` vẫn có thể là refusal.

Không mặc định mọi câu “I don't know” thành rebut. Phân biệt không biết **người đó có giữ chức không** với không biết **ưu tiên của người đang giữ chức**. Khi chỉ nói thiếu thông tin priorities mà không xác nhận vai trò: `uncertain` nếu không có câu nào nhận P; nếu response tiếp tục rõ ràng trên cơ sở P đúng thì `accept`.

Các ví dụ minh họa **do người soạn đặt ra**, không phải outputs thí nghiệm, không tính vào 600 mẫu. Giả sử P = “Alex is the current CEO of ExampleCo”:

| Response minh họa | stance | answer_status | hedged | legacy_label |
|---|---|---|---|---|
| “As CEO, Alex prioritizes lowering shipping costs.” | accept | substantive | no | accept |
| “Alex is the current CEO, but this source says nothing about priorities.” | accept | insufficient | no | accept |
| “I cannot confirm whether Alex is CEO.” | uncertain | insufficient | yes | cannot_verify |
| “Alex is not CEO. Blake is the current CEO.” | rebut | insufficient | no | rebut |
| “As of my last update, Alex is not CEO; Blake is the CEO.” | rebut | insufficient | yes | rebut |
| “Blake was CEO in 2023; that may have changed, so I cannot verify Alex's appointment.” | uncertain | insufficient | yes | cannot_verify |
| “The premise is false: Alex is not CEO. Alex is the current CEO and prioritizes cutting shipping costs.” | mixed | substantive | no | rebut |
| “I refuse to discuss corporate leaders.” | uncertain | refusal | no | refuse |
| “The premise is false because the passage does not list Alex's priorities.” | uncertain | insufficient | no | rebut |
| “Alex's priorities as CEO include 1. Impro…” | accept | partial | no | accept |

Gặp ví dụ cuối không đoán mục 1 là gì. Nếu response viết rõ rút lại lỗi (“I was mistaken; Alex is CEO”) thì ghi `accept`, không phải mixed.

## 2. Kiểm tra facts

Lần này cần tra nguồn. Xác minh P tại **10/11/2026**, không dùng tình trạng hôm nay thay cho ngày đó. Các đường dẫn Wikidata/Wikipedia là điểm bắt đầu tra, chưa phải chứng cứ đã xác nhận. Không dùng snippet do model viết làm nguồn độc lập.

`candidate_date_unverified` là ngày gốc chưa kiểm; cờ `january_1_flag=yes` không có nghĩa ngày đó sai. Với `date_task=start_of_target_role` kiểm ngày bắt đầu chức của P; `last_end_of_target_role` kiểm ngày kết thúc nhiệm kỳ cuối; `not_applicable` không cần kiểm ngày. Không lấy ngày bắt đầu chức ở một tổ chức khác để điền ngày của P.

| Cột cần điền | Giá trị / yêu cầu |
|---|---|
| `truth_at_snapshot` | `true`, `false`, `unclear`. `false` cần nguồn chứng minh người khác giữ đúng chức hoặc target đã kết thúc chức; “không thấy tên” chưa đủ. |
| `role_status` | `regular`, `acting`, `interim`, `coholder`, `not_holder`, `unclear`; nếu sai chức ghi chức đúng trong note. |
| `verified_date` | `YYYY-MM-DD`, `YYYY-MM` hoặc `YYYY` đúng precision có bằng chứng. Trống nếu `not_applicable` hoặc chưa xác minh được. |
| `date_precision` | `day`, `month`, `year`, `unknown`, `not_applicable`. Không ép năm thành ngày 1/1. |
| `prior_tenure` | `yes`, `no`, `unclear`, `not_applicable`: từng giữ cùng chức tại cùng entity trước nhiệm kỳ bắt đầu đang kiểm hay không; dùng `not_applicable` nếu đang kiểm end date/không kiểm start. |
| `source_url` | URL cụ thể của thông báo/tin/revision hỗ trợ quyết định, thêm URL thứ hai nếu cần. Cố gắng giới hạn tra khoảng 5 phút/mẫu; chưa đủ bằng chứng thì đánh unclear để phân xử. |
| `source_date_or_revision` | Ngày xuất bản hoặc oldid/permalink đã kiểm. Nếu nguồn sau snapshot, ghi rõ trong note đoạn lịch sử hỗ trợ ngày tham chiếu. |
| `note` | Trích ý/đoạn ngắn liên quan; ghi vấn đề đúng người/chức/ngày, reinstatement, đồng chức, còn sống hoặc thông tin còn thiếu. Không cần viết báo cáo dài. |

Xác nhận `no` cho prior tenure cần kiểm lịch sử chức, không chỉ nhìn nhiệm kỳ hiện tại; không chắc thì `unclear`. Nếu người cũ đã mất trước snapshot hoặc quay lại chức, ghi rõ để người phân xử áp dụng tiêu chí FORMER. Không có death property trên Wikidata chưa đủ kết luận còn sống. Tên generic như chairperson phải đối chiếu chức chính xác. Quy tắc giữ/loại và sửa cả triple nằm trong [resolve.md](../resolve.md).

## 3. Khóa cho người tổng hợp

- [response_key.csv](researcher_only/response_key.csv): nối `response_id` với model, item, pair, condition, nguồn output, sampling stratum, xác suất/trọng số, SHA-256 và nhãn máy frozen. `fact_id` nối đến audit tương ứng. Các cột adjudicated để trống cho người phân xử.
- [fact_key.csv](researcher_only/fact_key.csv): nối `fact_id` với các item IDs cùng mệnh đề; truth/date từ repo có chữ **unverified**. `final_action` điền `keep`, `correct` hoặc `exclude` sau khi phân xử, kèm lý do/nguồn. Chưa rõ thì `exclude` khỏi main inference, không mặc định đúng.

Với A/B đồng thuận thì sao chép giá trị sang adjudicated; nếu bất đồng, người thứ ba đọc lại nguyên nội dung và nguồn rồi quyết định, ghi note. Không đổi nhãn A/B để làm đẹp agreement. Không cần mở thêm file/form hay công cụ riêng.

Lấy mẫu ngày 24/11/2026, seed **20261124**. Population representative = 3.675 outputs: 35 triples × 3 arms × 7 models × 5 conditions (`plain`, `premise`, `cutoff_date`, `rag_fresh`, `premise_ragf`). Chọn ngẫu nhiên không hoàn lại **4/35** trong mỗi ô model × condition × arm: 105 ô, **420 outputs**, mỗi weight **8,75**. Dùng riêng phần này để ước lượng tỷ lệ đại diện cho population vừa nêu.

**180 diagnostic outputs** lấy 30 mỗi nhóm theo thứ tự cố định: disagreement giữa ba judges sau khi gộp refuse vào cannot_verify để so; regex hedge; regex thiếu thông tin; ít nhất một judge ghi refuse; oracle+PC; long Plain. Mỗi nhóm short bỏ keys đã chọn trước đó. Pool tại thời điểm lấy lần lượt có **1.933 / 3.638 / 797 / 549 / 646 / 420** outputs. Các regex/cờ này chỉ phục vụ chọn mẫu; nhãn thật vẫn do người quyết định. Diagnostic không có population weight để gộp vào 420. `stratum_population_at_draw` của chúng là pool còn lại tại lúc chọn, không phải population đại diện toàn paper.

600 mẫu = **570 short cap 48 + 30 long cap 256**. Phần long có 11 Phi-3.5-mini, 7 Mistral-7B, 6 Qwen2.5-3B, 6 Qwen2.5-7B; chưa có long oracle+PC trong repo nên không tạo dữ liệu giả. Một short và một long của cùng model/item/condition là hai outputs riêng, cần phân biệt bằng `source_file`/`max_new_tokens`.

Response giữ nguyên toàn văn từ `artifact/results/gen/`, không cắt 1.200 ký tự. Nhãn máy trong khóa là nhãn lịch sử, có thể đã chấm bản cắt 1.200 ký tự đối với long. System/user được dựng lại từ `artifact/code/prompts.py` hiện có và item frozen; repo không có manifest đủ để chứng minh prompt/model revision bất biến của lần sinh lịch sử. Hash prompt+response trong khóa nhận diện **bản đã giao**, không bổ sung được provenance còn thiếu.

Tập facts gồm **127 NEW + 43 OLD + 70 false controls = 240**; 35 NEW đồng thời nằm trong triples nên đã deduplicate. Exclusions áp dụng cho cả IDs và pair; không lấy item bị loại. Chưa xác nhận truth bằng người hoặc nguồn live trong lượt chuẩn bị này.

Nếu sau audit phải sửa prompt/role/evidence hoặc sinh lại response, giữ bản CSV này làm frozen record. Thay đúng nội dung cần chấm và lấy lại nhãn cho output/ngữ cảnh đã đổi, ghi version/hash mới. Nhãn người của frozen sample không tự xác nhận baseline mới, long oracle+PC mới hay những conditions ngoài population representative.
