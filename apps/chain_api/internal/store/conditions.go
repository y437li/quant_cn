package store

// ConditionResult is one structured condition (plan 15 ph7f) evaluated in Python by
// ConditionEvaluator: the threshold, the value found (null when unknown) and the state.
type ConditionResult struct {
	Label  string   `json:"label"`
	Kind   string   `json:"kind"`
	Metric string   `json:"metric"`
	Op     string   `json:"op"`
	Value  float64  `json:"value"`
	Actual *float64 `json:"actual"`
	State  string   `json:"state"`
	// Required conditions must be met whatever conditions_needed says (plan 15 ph7n).
	Required bool `json:"required"`
}

// PositionNote is the user's note on a held stock (config/local.positions.yaml `notes`).
type PositionNote struct {
	Thesis    string   `json:"thesis"`
	Falsifier string   `json:"falsifier"`
	Stop      *float64 `json:"stop"`
	Target    *float64 `json:"target"`
	Action    string   `json:"action"`
	Watch     string   `json:"watch"`
	Reviewed  string   `json:"reviewed"`
}

// ReviewFlag is one alert on a position: stop, target, weight, review or note.
type ReviewFlag struct {
	Kind    string `json:"kind"`
	Message string `json:"message"`
}

// PositionReview is PositionReviewer's row for one held stock: note, flags, the 筹码结构 and
// statement row (null numbers when unknown), the latest statement period and the conditions.
type PositionReview struct {
	Note       *PositionNote       `json:"note"`
	Flags      []ReviewFlag        `json:"flags"`
	Chips      map[string]*float64 `json:"chips"`
	Period     *string             `json:"period"`
	Conditions []ConditionResult   `json:"conditions"`
}

func fillReview(r PositionReview) PositionReview {
	if r.Flags == nil {
		r.Flags = []ReviewFlag{}
	}
	if r.Chips == nil {
		r.Chips = map[string]*float64{}
	}
	if r.Conditions == nil {
		r.Conditions = []ConditionResult{}
	}
	return r
}
