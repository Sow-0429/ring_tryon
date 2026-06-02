package application

import (
	"context"
	"testing"

	"github.com/google/uuid"

	billingdomain "github.com/Sow-0429/ring_tryon/internal/billing/domain"
)

func TestStaticEntitlementPolicy_TierFor(t *testing.T) {
	premiumUser := uuid.New()
	standardUser := uuid.New()
	policy := NewStaticEntitlementPolicy(premiumUser)

	t.Run("premiumユーザーはpremium", func(t *testing.T) {
		if got := policy.TierFor(context.Background(), premiumUser); got != billingdomain.TierPremium {
			t.Errorf("TierFor = %v, want premium", got)
		}
	})

	t.Run("既定はstandard", func(t *testing.T) {
		if got := policy.TierFor(context.Background(), standardUser); got != billingdomain.TierStandard {
			t.Errorf("TierFor = %v, want standard", got)
		}
	})
}
