name: Feature Request
description: Đề xuất feature mới
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: Mô tả feature bạn muốn

  - type: textarea
    id: problem
    attributes:
      label: Vấn đề cần giải quyết
      placeholder: Vấn đề gì? Ai gặp? Tần suất?
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Giải pháp đề xuất
      placeholder: Bạn muốn nó hoạt động thế nào?
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      placeholder: Cách khác bạn đã nghĩ?

  - type: textarea
    id: context
    attributes:
      label: Context
      placeholder: Use case, screenshot, etc.
