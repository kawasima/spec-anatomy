# 現代の仕様駆動開発の理解

Spec-Driven Development（SDD、仕様駆動開発）は、2025年に名前のついたプラクティスとして広がった。コーディングエージェントに良いコードを出させるには、実装前に「何を・なぜ作るか」を仕様として書いて渡すべきだ、という考え方である。Thoughtworksは SDD を[「よく練られたソフトウェア要求仕様をプロンプトとして使い、AIコーディングエージェントの助けを借りて実行可能なコードを生成するパラダイム」](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)と定義する。Microsoftの整理では、[ガードレール・要件・制約・受け入れ基準・エッジケースを事前に定義し、その共有コンテキストからAIがコード・テスト・成果物を生成する spec-first のアプローチ](https://developer.microsoft.com/blog/spec-driven-development-ai-native-engineering)だとされる。

このドキュメントは、2024年から2026年にかけて出た論文・記事・ツールを論点ごとに整理したものである。現代のSDDが何を主張し、どこで意見が分かれているかを把握するために置く。末尾に出典を一覧する。

## なぜ今SDDなのか

背景にあるのはコストの変化である。コード生成のコストが大きく下がり、作業の中心が「コードを書くこと」から「意図を言語化すること」に移った。[ASDLCフレームワークはこれを「Intent Debt（意図の負債）」と呼び](https://asdlc.io/patterns/the-spec/)、意図を明示しないまま生成を進めると、エージェントがコメントやコミットメッセージから意図を逆算し、ハルシネーションとアーキテクチャドリフトを招くとする。SDDは、要件分析・設計・アーキテクチャ制約・人間によるガバナンスを再導入することで、いわゆる vibe coding の弱点を補うものだと[Thoughtworksは位置づける](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)。

もっとも強い主張をしているのが、取引コスト経済学でSDDを基礎づけた[2026年5月の論文](https://arxiv.org/pdf/2605.01160)である。この論文の中心的な主張は、AI支援ソフトウェアの信頼性を決めるのは、基盤となるAIモデルの能力ではなく仕様の規律だ、というものである。モデルを大きくするより仕様を厳密にするほうが効果が大きい、という立場だ。同論文は非決定的なコード生成を「高い資産特殊性と行動的不確実性」を持つ取引ととらえ、決定論的な仕様を契約的ガバナンスの仕組みとして扱う。

ただし証拠は一致していない。同論文自身が、対照実験では20〜56%の生産性向上が報告される一方、[METRのランダム化比較試験](https://arxiv.org/pdf/2605.01160)では熟練OSS開発者16名がAIツールで19%遅くなった（本人たちは24%速くなると予想していた）ことを引いている。1万人超のテレメトリでは、マージされたPRが98%増える一方でレビュー時間が91%伸び、デリバリ指標は横ばいだった。SDDが効くという主張は、こうした相反する観測を踏まえて慎重に読む必要がある。

## 3つの成熟度: spec-first / spec-anchored / spec-as-source

現代SDDを理解する中心にあるのは、Birgitta Böckelerが2025年10月に示した[3段階の成熟度分類](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)である。

| 段階 | 仕様の扱い |
| --- | --- |
| spec-first | 開発前に仕様を書く。実装後は保守されない |
| spec-anchored | 仕様が機能とともに残り、進化し続ける |
| spec-as-source | 仕様が主要成果物。人間は生成コードを編集しない |

この三分類は、[2026年1月のPiskalaのarXiv論文](https://arxiv.org/html/2602.00180v1)でも Spec-First / Spec-Anchored / Spec-as-Source として形式化されており、最上位では仕様が人間の編集する唯一の成果物で、コードは完全な生成物とされる。Piskalaはコードと仕様の従来の関係を反転させ、仕様を一次成果物、コードを下流の実装詳細と位置づける。Living Documentationは spec-anchored のアプローチ、つまりBDDシナリオを毎コミット実行して仕様とコードの乖離を検出するような仕組みで達成される、というのがPiskalaの整理である。

Böckelerが調べた3ツールは別々の段階に位置する。[Kiro は spec-first のみ、GitHubの spec-kit は spec-anchored を志向するが実態は spec-first、Tessl だけが spec-anchored と spec-as-source を明示的に追求していた](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)。Tesslの spec-as-source は、1つの仕様を1つのコードファイルに対応させ、`@generate` や `@test` のタグで生成し、出力に `GENERATED FROM SPEC - DO NOT EDIT` を書き込む方式だった。

Böckelerはここに警告を加えている。spec-as-source は、モデル駆動開発（MDD）の硬直性とLLMの非決定性を併せ持つ危険がある。MDDが現実の複雑さに対してモデルが硬すぎたために一度失敗した歴史を、繰り返しかねないという指摘だ。なお[specdriven.comのランドスケープ記事](https://specdriven.com/landscape/)はこの三分類をMartin Fowlerに帰属させているが、原典はFowlerのサイトに掲載されたBöckelerの記事であり、分類の主はBöckelerである。

## Source of Truth はどこにあるか

3段階の分類が生む最大の争点は、Source of Truth（SoT）をどこに置くかである。[Thoughtworksはこれを未決着の論争として明示している](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)。仕様が保守すべき唯一の成果物になるのか、それとも実行可能なコードが依然としてSoTであり続けるのか。この対立は spec-first と spec-as-source の対立とほぼ重なる。

技術仕様から生成したコードは、平文の要件から生成したコードより品質が高い、という観察は複数のソースで一致している（[Thoughtworks](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)）。半構造化された入力や構造化出力の強制がLLMの推論を改善しハルシネーションを減らす、という[別のThoughtworks記事](https://thoughtworks.medium.com/spec-driven-development-d85995a81387)の指摘も同じ方向である。だからといって仕様をSoTに固定できるかは別問題で、ここが論争の中心になっている。

spec-anchored 側の具体策として出てきたのが「living specs（生きた仕様）」である。[Augment Codeは、静的な仕様は情報が一方向にしか流れない（開発者が書き、エージェントが読み、仕様は放置される）ためドリフトが再生成のたびに積み重なると指摘し](https://www.augmentcode.com/guides/living-specs-for-ai-agent-development)、実装判断を仕様に書き戻す双方向のワークフロー（Intent / Implementation / Update / Refinement）を提案する。マルチエージェント開発では、仕様は単なるドキュメントではなく、要件と制約を保持する調整インフラとして機能するという。[ASDLCも同様に、仕様をリポジトリに置く一級の開発成果物とし](https://asdlc.io/patterns/the-spec/)、仕様（現在の状態を記述）とPBI（変更差分を記述）を役割分担させて、将来のエージェントが持続的なアーキテクチャルールを参照できるようにする。

## spec-first への批判: Waterfall回帰とスケール破綻

現代SDDには一貫した批判がある。論点は「ウォーターフォールへの回帰」「仕様ドリフト」「大規模・既存コードでの破綻」の3つである。

もっとも直接的なのがMarmelabの[「The Waterfall Strikes Back」](https://marmelab.com/blog/2025/11/12/spec-driven-development-waterfall-strikes-back.html)である。著者はSDDが既存の大規模コードベースではほとんど使えないとし、開発者を工程から排除しようとするウォーターフォールへの回帰だと論じる。SDDエージェントはコンテキスト認識を欠き、更新すべき既存コードを見落とす。代替として、形式的な spec-first ワークフローに従わない反復的なアプローチ「Natural Language Development」を提案している。

より構造的な批判が[Arcturus Labsの「Why spec-driven development breaks at scale」](http://arcturus-labs.com/blog/2025/10/17/why-spec-driven-development-breaks-at-scale-and-how-to-fix-it/)にある。現行の主流SDDは仕様を使い捨てにしている（コード変更の前に書き、実装が終われば捨てる）。そして大きな自然言語仕様はスケールで破綻する。自然言語は本質的に曖昧で、仕様を完全に曖昧さのない状態まで詳細化すると、それはコードと等価になり、仕様である利点を失う。著者の提案は、一発の仕様→コード生成ではなく開発者とエージェントの対話的な明確化を行うこと、モノリシックな仕様ではなく階層的にリンクした文書（グローバル仕様がサブ仕様にリンクする）にすること、そしてコード変更が仕様更新を駆動する living document にして、コードが仕様と食い違うたびに同じPRでグローバル仕様を編集することである。

[sudoishの「The Spec-Driven Development Waterfall Trap」](https://sudoish.com/spec-driven-development-waterfall-trap/)も同じ問題を指摘する。SDDは本来反復的・アジャイルであるべきだが、ワークフローのガードレールと十分なツールがなければ、既定でウォーターフォール的な big-design-upfront に退行する。加えてAI生成の仕様は信頼性の問題を抱える。出力は権威ありげに見えるが真に推論されたものではなく、AIが反論されると、自分が最初から持っていなかった立場と辻褄を合わせようとしてハルシネーションのリスクが上がる。

さらに歴史的な後退を指摘するのが[specdriven.comのランドスケープ整理](https://specdriven.com/landscape/)である。2026年初頭時点の主要ツール（Kiro / GitHub Spec Kit / OpenSpec / BMAD / IntentSpec）はいずれも非実行のMarkdown散文を仕様形式としており、BDD時代（FIT / Cucumber / RSpec）が達成していた実行可能仕様から後退している、という整理である。実際、[Specification by Example を使ってAIを駆動する実験](https://urgo.medium.com/using-specification-by-example-to-drive-ai-95c19f0bb4ec)では、Gherkin/実行可能仕様はアドホックなプロンプトより検証可能だが、AIはテストが正しい理由で落ちたかを判別しにくく、シナリオが複雑化するとBDDのグルーコード品質が劣化した。実行可能仕様への回帰も、それ自体が万能ではない。

## 機械可読仕様とLiving Documentation

「AIが読むためのドキュメント」という論点は、Cyrille Martraireの Living Documentation（2019）にさかのぼる。[InfoQの書評](https://www.infoq.com/articles/book-review-living-documentation/)がまとめる核は、ドキュメントを対象そのもの（コード要素へのアノテーションなど）に置いて実装と同期させること、ドメイン知識はコード・テスト・実行時の挙動にすでに潜在しており、手作業の転記ではなく自動抽出で表面化させること、である。これが機械可読／AI可読な仕様の起点にあたる。

この考え方はLLM時代に不要になるどころか、重要性が増す。[Thoughtworksは、自然言語を扱えるモデルが登場しても機械可読仕様は依然として本質的だと述べ](https://thoughtworks.medium.com/spec-driven-development-d85995a81387)、半構造化された入力プロンプトや構造化出力の強制が推論性能を大きく改善しハルシネーションを減らすとする。ツール（Amazon Kiro、GitHub Spec Kit）は定義済みのSDDワークフローを提供し、コーディングエージェントは `AGENTS.md` をシステムプロンプトとして使う。

ただし、仕様を詳細にすればするほど良いわけではない。[Addy Osmaniは、GitHubが2,500以上のエージェント設定ファイルを分析して抽出した仕様の6要素](https://addyosmani.com/blog/good-spec/)（コマンド、テストのフレームワークとカバレッジ、プロジェクト構造、コードスタイルの例、gitワークフロー、境界＝Always / Ask First / Never の3層）を紹介しつつ、指示を詰め込むほどモデルの追従性が劣化する「curse of instructions」を指摘する。だから仕様はモジュラーに保ち、エージェントには一度に一つの焦点を絞ったタスクを渡す。高レベルの簡潔な仕様から始め、AIにそれを詳細な計画へ展開させるのがよく、最初から完全な計画を作り込むのは過剰だ、という。

## 検証: 相関エラーと決定論的ゲート

生成が安くなるほど、もっともらしいが間違った仕様・実装・テストが増える。だから検証の重要性はむしろ上がる。[Thoughtworksは、SDDにおいても仕様ドリフトとハルシネーションは本質的に避けがたく、決定論的なCI/CDプラクティスが依然として必要だと明言している](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)。

学術側はこの検証を主題にし始めている。SANER 2026に採択された[CURRANTE（registered report）](https://arxiv.org/html/2601.03878v1)は、LLMのコード生成を Specification → Tests → Function の3段に構造化するVS Codeプラグインで、仕様とテストの精緻化に人間が介入することが生成コードの品質とダイナミクスに影響するかを実証的に調べる。要件・仕様のエンジニアリングに労力を投じるのと、コードの精緻化に投じるのとのトレードオフを明らかにする設計である。

形式検証と組み合わせる方向もある。[2024年11月のspec2code](https://arxiv.org/abs/2411.13269)は、形式仕様（ACSL）と自然言語仕様をLLMに与えて組込み自動車ソフトを生成し、安全クリティカル領域向けに形式検証を統合する。反復的なbackpromptとfine-tuningによる精緻化を前提とし、重量車メーカーScaniaの3つの産業事例で検証されている。

検証を仕様の中核に据えたのが前掲のTDAD論文である。[TDAD（Test-Driven AI Agent Definition）パイプラインは、行動仕様を実行可能なテストスイートにコンパイルし、AI生成のエージェントプロンプトの受け入れ基準として使う](https://arxiv.org/pdf/2605.01160)。4ドメインで86〜100%のミューテーションスコアを達成したという。

検証設計でとくに危ういのは、実装とテストを同じ仕様から同時に生成させるケースである。仕様を同じ方向に誤解すると、実装もテストも同じバグを共有する。この相関エラーへの対策として、人間が定義した具体的な入出力の受け入れテストを併用すること、テストの源泉を実装と異なる入力（外部契約・画面モックなど）に置くことが、実務側の記事でも繰り返し推奨されている。

## ツールの現状

学術的なサーベイもツール群の整理に入っている。[2026年6月の論文](https://arxiv.org/pdf/2606.04967)は、AI開発フレームワークを specification / context / roles / execution / validation / portability の6次元で分類し、6次元すべてを強くカバーするフレームワークは存在せず、プロセスの深さと（エージェント間の）可搬性のあいだにトレードオフがあることを実証的に見出した。GitHub APIで「1000スター以上かつ直近6ヶ月にpushあり」というトラクションフィルタをかけて選んだ6フレームワークは、GitHub Spec Kit（106,786スター）、Get Shit Done（63,754）、OpenSpec（51,404）、BMAD Method（48,209）、Spec Kitty（1,273）、Reversa（1,100）である。Reversaは、既存のレガシーシステムから運用仕様を復元する reverse documentation engineering によって、通常のグリーンフィールドSDDの向きを反転させる。

主要ツールを整理すると次のようになる。

| ツール | 提供元・形式 | ワークフロー / 位置づけ |
| --- | --- | --- |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | GitHub/Microsoft、MITライセンスのMarkdownテンプレート、2025年9月 | constitution → specify → clarify → plan → tasks → implement。各フェーズがMarkdown成果物を生成。エージェント非依存で30以上のコーディングエージェントに対応、106K★、105のコミュニティ拡張。仕様をバージョン管理された使い捨てでない source of truth として扱う |
| [Kiro](https://kiro.dev/blog/introducing-kiro/) | AWS、EARS記法を用いるMarkdown、2025年7月 | Requirements → Design → Tasks。要求はEARS（Easy Approach to Requirements Syntax）記法のユーザーストーリー、設計はコードベース解析からデータフロー図・TypeScript interface・DBスキーマ・APIを生成。ファイル保存等をトリガーにする agent hooks |
| OpenSpec | Fission AI、Markdown+YAML、ブラウンフィールド向け | 仕様を凍結ではなく可変（mutable）として扱う |
| BMAD-METHOD | コミュニティ、複数成果物のMarkdown | 仕様・計画・タスクリストを生成してエージェントを駆動 |
| Tessl | 2025年9月に Tessl Framework と Spec Registry で参入 | spec-as-source を追求した唯一のツールだったが、2026年1月にエージェントスキルへ方針を変え、Spec RegistryをTessl Registryに改称してSDDカテゴリから撤退 |

Spec Kitのワークフローは、仕様を「実装を導くもの」から「実装を直接生成する実行可能な成果物」へ捉え直す点に特徴がある（[公式ガイド](https://github.github.com/spec-kit/)）。「何を・なぜ（仕様）」と「どう（技術計画・技術スタック）」を分離し、specifyフェーズでは技術スタックの詳細を意図的に除く。一発生成ではなく多段の反復的な精緻化を選ぶ。

Tesslの撤退（2025年9月参入、2026年1月にSDDカテゴリから離脱、[specdriven.com](https://specdriven.com/landscape/)）は、spec-as-source の商業的な難しさを示す事例である。

## 次に問うべきこと

ここまでが調査で得た現代SDDの整理である。論点は出ている。SoTを仕様とコードのどちらに置くか、spec-first をどこまで許すか、機械可読仕様と自然言語仕様をどう配分するか、検証をどの層に置くか。次は、これらの論点に対して自分の立場を書き入れ、ドメイン記述ミニ言語やユビキタス言語の議論（[ubiquitous_language.md](./ubiquitous_language.md) 参照）とどう接続するかを考えていく。

## 出典一覧

### 学術論文（arXiv / 査読）

- [spec2code: 形式仕様（ACSL）と自然言語仕様からの組込み自動車ソフト生成、形式検証と統合、Scania事例](https://arxiv.org/abs/2411.13269)（2024-11）
- [Piskala: SDDの3段階形式化（Spec-First / Spec-Anchored / Spec-as-Source）](https://arxiv.org/html/2602.00180v1)（2026-01）
- [CURRANTE: LLMコード生成を Specification→Tests→Function に構造化するVS Codeプラグイン、SANER 2026](https://arxiv.org/html/2601.03878v1)（2026-01）
- [AI開発フレームワークの6次元プロセス分類とトラクションフィルタによる6フレームワーク比較](https://arxiv.org/pdf/2606.04967)（2026-06）
- [TDAD: 取引コスト経済学によるSDDの基礎づけ、「決めるのは仕様の規律でありモデル能力ではない」](https://arxiv.org/pdf/2605.01160)（2026-05）

### ツール公式・一次資料

- [GitHub Spec Kit（リポジトリ）](https://github.com/github/spec-kit) / [公式ガイド](https://github.github.com/spec-kit/)（2025-09、MIT）
- [Kiro（AWS）introducing-kiro](https://kiro.dev/blog/introducing-kiro/)（2025-07）

### 方法論・著名エンジニアのブログ

- [Birgitta Böckeler「Understanding Spec-Driven Development（3ツール）」— 3成熟度分類の原典](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)（2025-10）
- [Addy Osmani「What makes a good spec?」— 仕様の6要素、curse of instructions](https://addyosmani.com/blog/good-spec/)（2026-01）
- [Microsoft Dev Blog「Spec-Driven Development: AI-Native Engineering」— 7ステップ、translation loss](https://developer.microsoft.com/blog/spec-driven-development-ai-native-engineering)（2026-06）
- [Thoughtworks「Spec-Driven Development: unpacking 2025's new practice」— SoT論争、決定論ゲート](https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices)（2025-12）
- [Thoughtworks（Medium）「Spec-Driven Development」— 機械可読仕様の必要性、AGENTS.md](https://thoughtworks.medium.com/spec-driven-development-d85995a81387)（2025-12）
- [ASDLC「The Spec」— living spec、context amnesia、Intent Debt](https://asdlc.io/patterns/the-spec/)（2026-04）
- [Augment Code「Living Specs for AI Agent Development」— 双方向ワークフロー、仕様ドリフト](https://www.augmentcode.com/guides/living-specs-for-ai-agent-development)（2026-03）

### Living Documentation

- [InfoQ「Book Review: Living Documentation」（Cyrille Martraire）— 機械可読/AI可読仕様の起点](https://www.infoq.com/articles/book-review-living-documentation/)（2019）

### 批判・限界論

- [Marmelab「The Waterfall Strikes Back」— 既存大規模コードで破綻、Natural Language Development](https://marmelab.com/blog/2025/11/12/spec-driven-development-waterfall-strikes-back.html)（2025-11）
- [Arcturus Labs「Why SDD breaks at scale and how to fix it」— 階層的リンク仕様、living document](http://arcturus-labs.com/blog/2025/10/17/why-spec-driven-development-breaks-at-scale-and-how-to-fix-it/)（2025-10）
- [sudoish「The Spec-Driven Development Waterfall Trap」— BDUF退行、AI仕様の信頼性問題](https://sudoish.com/spec-driven-development-waterfall-trap/)（2026-04）
- [urgo「Using Specification by Example to drive AI」— Gherkinでの実験、BDDグルーコードの劣化](https://urgo.medium.com/using-specification-by-example-to-drive-ai-95c19f0bb4ec)（2025-11）

### ランドスケープ整理

- [specdriven.com「SDD Landscape」— 非実行Markdownへの後退、ツール系譜、Tessl撤退](https://specdriven.com/landscape/)（2026）

### 補足: 検証で否認された主張

以下は情報源自体は有効だが、特定の数値・帰属が敵対的検証（3票制）で否認されたため、本文では採用していない。

- spec2code論文について「LLMはbackpromptもfine-tuningもなしに仕様のみから形式的に正しいコードを生成できる」という過剰一般化（実際は反復精緻化を前提とする）
- Piskala論文について「エラー最大50%削減の対照実験」という裏付けの取れない数値
- specdriven.comの「Martin Fowlerが3パターンに分類」という誤帰属（正しくはBirgitta Böckeler）
