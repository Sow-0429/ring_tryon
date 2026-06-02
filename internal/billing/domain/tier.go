// Package domain は課金ティアのドメインモデル。
package domain

// Tier は計測の品質ティア。standard は全機種、premium は深度センサ(買い切り)。
type Tier string

const (
	TierStandard Tier = "standard"
	TierPremium  Tier = "premium"
)

func (t Tier) String() string {
	return string(t)
}
