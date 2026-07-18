# Contributing

## Welcome!

Đây là dự án open source, mọi đóng góp đều được hoan nghênh.

## Cách đóng góp

### Báo bug
1. Search [Issues](https://github.com/xservices-git/ai-employee/issues) trước
2. Tạo issue mới với template `bug_report.md`
3. Kèm: version, OS, log, steps to reproduce

### Đề xuất feature
1. Tạo issue với template `feature_request.md`
2. Mô tả use case rõ ràng
3. Đợi maintainer review trước khi code

### Gửi PR
1. Fork repo
2. Tạo branch: `git checkout -b feat/my-feature`
3. Code + test
4. Đảm bảo CI pass: `make ci`
5. Push + tạo PR với template

## Code style

### Python
- Format: `ruff format`
- Lint: `ruff check`
- Type check: `mypy --strict`
- Test: `pytest`

```python
# Good
def calculate_confidence(task: Task) -> float:
    """Calculate confidence score for a task."""
    return min(1.0, task.success_rate * 0.8)

# Bad
def calc(t):
    return min(1, t.s * 0.8)
```

### TypeScript
- Format: `prettier`
- Lint: `eslint`
- Type check: `tsc --noEmit`
- Test: `vitest`

### Go
- Format: `gofmt`
- Lint: `golangci-lint`
- Test: `go test`

### Commit message
Format: `<type>(<scope>): <subject>`

```
feat(orchestrator): add Critic agent for self-review
fix(memory): handle ChromaDB connection timeout
docs(roadmap): update M3 deliverables
test(eval): add 20 cases for sales_ops domain
refactor(api): split routes by domain
chore(deps): bump fastapi to 0.115
```

## PR checklist

- [ ] Code follow style guide
- [ ] Có test cho thay đổi
- [ ] All test pass: `make test`
- [ ] Lint pass: `make lint`
- [ ] Type check pass: `make typecheck`
- [ ] Update docs nếu thay đổi public API
- [ ] Update CHANGELOG.md
- [ ] 1 approval từ maintainer

## Quy trình review

1. Maintainer review trong 3 ngày
2. Có thể có nhiều round review
3. Khi approved → squash merge vào master
4. Auto deploy dev environment
5. Test 1 ngày → promote staging
6. Test 3 ngày → production

## Coding principles

### Ponytail mode (lazy senior dev)
- YAGNI: không build tính năng chưa cần
- Stdlib first: dùng thư viện chuẩn
- No unrequested abstractions
- KISS > clever
- Code đọc được quan trọng hơn code ngầu

### Khi nào review cho là "OK"?
- Test cover happy path + edge case
- Không có dead code
- Không có TODO không giải thích
- Log ở điểm quan trọng (không spam)
- Error message có action: "X làm Y để fix"
- Không break backward compatibility (trừ major version)

## Architecture decisions

Mọi thay đổi kiến trúc lớn cần có ADR (Architecture Decision Record):

```markdown
# ADR-001: Tại sao dùng multi-agent thay vì 1 agent

## Context
Cần quyết định cách organize logic xử lý task.

## Decision
Dùng 5 agents riêng biệt (Planner, Executor, Critic, Memory Curator, Supervisor).

## Consequences
+ Separation of concerns
+ Dễ test từng phần
+ Scale độc lập
- Overhead communication
- Cần A2A protocol

## Alternatives considered
- 1 single agent: fail vì không tách được concern
- 2 agents (Planner + Executor): thiếu Critic
```

Lưu vào `docs/adr/`.

## Community

- GitHub Discussions: cho câu hỏi, ý tưởng
- GitHub Issues: cho bug, feature
- Telegram group: (sẽ tạo khi có đủ người)

## Code of Conduct

- Tôn trọng mọi người
- Không dung thứ harassment
- Focus vào technical merit
- Giúp đỡ người mới

## License

MIT - xem `LICENSE`.

Bạn có thể dùng, sửa, phân phối thương mại, miễn là giữ copyright notice.
