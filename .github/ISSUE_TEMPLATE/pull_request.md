name: Pull Request
description: Tạo Pull Request
body:
  - type: markdown
    attributes:
      value: Cảm ơn bạn đã contribute!

  - type: input
    id: related
    attributes:
      label: Related issue
      placeholder: "#123"

  - type: textarea
    id: what
    attributes:
      label: What changed
      placeholder: Mô tả thay đổi
    validations:
      required: true

  - type: textarea
    id: testing
    attributes:
      label: Testing
      placeholder: |
        - [ ] Unit tests pass
        - [ ] Integration tests pass
        - [ ] Manual testing
    validations:
      required: true

  - type: textarea
    id: breaking
    attributes:
      label: Breaking changes
      placeholder: Nếu có breaking change, mô tả ở đây
