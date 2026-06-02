// Package application は課金・エンタイトルメントのユースケース。
// 課金判定はアプリ層に閉じ、計測/ユーザーのドメインには混ぜない(ADR-0005)。
package application

import (
	"context"

	"github.com/google/uuid"

	billingdomain "github.com/Sow-0429/ring_tryon/internal/billing/domain"
)

// EntitlementPolicy はユーザーが利用できるティアを判定するポート。
type EntitlementPolicy interface {
	TierFor(ctx context.Context, userID uuid.UUID) billingdomain.Tier
}

// StaticEntitlementPolicy は premium ユーザー集合を静的に持つ単純な実装。
// 将来は課金プロバイダ連携の実装に差し替える。
type StaticEntitlementPolicy struct {
	premium map[uuid.UUID]struct{}
}

func NewStaticEntitlementPolicy(premiumUsers ...uuid.UUID) *StaticEntitlementPolicy {
	set := make(map[uuid.UUID]struct{}, len(premiumUsers))
	for _, id := range premiumUsers {
		set[id] = struct{}{}
	}
	return &StaticEntitlementPolicy{premium: set}
}

func (p *StaticEntitlementPolicy) TierFor(
	_ context.Context, userID uuid.UUID,
) billingdomain.Tier {
	if _, ok := p.premium[userID]; ok {
		return billingdomain.TierPremium
	}
	return billingdomain.TierStandard
}
