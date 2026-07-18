name: Bug Report
description: Báo bug
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: Cảm ơn bạn đã báo bug!

  - type: input
    id: version
    attributes:
      label: Version
      placeholder: "0.1.0"
    validations:
      required: true

  - type: textarea
    id: what
    attributes:
      label: Mô tả bug
      placeholder: Bug là gì?
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: Steps to reproduce
      placeholder: |
        1. ...
        2. ...
        3. ...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Logs
      placeholder: Paste log liên quan
