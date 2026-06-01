package domain

import (
	"math"
	"testing"
)

func TestNewRingSize(t *testing.T) {
	t.Run("正の周囲長で生成できる", func(t *testing.T) {
		// Arrange & Act
		rs, err := NewRingSize(50.5)

		// Assert
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if rs.CircumferenceMM() != 50.5 {
			t.Errorf("got %f, want 50.5", rs.CircumferenceMM())
		}
	})

	t.Run("ゼロの周囲長はエラー", func(t *testing.T) {
		// Arrange & Act
		_, err := NewRingSize(0)

		// Assert
		if err == nil {
			t.Fatal("expected error for zero circumference")
		}
	})

	t.Run("負の周囲長はエラー", func(t *testing.T) {
		// Arrange & Act
		_, err := NewRingSize(-1)

		// Assert
		if err == nil {
			t.Fatal("expected error for negative circumference")
		}
	})
}

func TestRingSize_JPSize(t *testing.T) {
	tests := []struct {
		name            string
		circumferenceMM float64
		wantJP          int
	}{
		{"1号の下限付近", 41.0, 1},
		{"10号ちょうど", 50.5, 10},
		{"13号ちょうど", 53.5, 13},
		{"25号ちょうど", 66.0, 25},
		{"7号と8号の間", 48.0, 8},
		{"1号より小さい", 38.0, 1},
		{"25号より大きい", 70.0, 25},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			rs, err := NewRingSize(tt.circumferenceMM)
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}

			// Act
			got := rs.JPSize()

			// Assert
			if got != tt.wantJP {
				t.Errorf("JPSize() = %d, want %d (circumference=%.1f)", got, tt.wantJP, tt.circumferenceMM)
			}
		})
	}
}

func TestRingSize_JPSizeRange(t *testing.T) {
	t.Run("中間の号数", func(t *testing.T) {
		// Arrange
		rs, _ := NewRingSize(50.5) // 10号

		// Act
		low, high := rs.JPSizeRange()

		// Assert
		if low != 9 || high != 11 {
			t.Errorf("JPSizeRange() = (%d, %d), want (9, 11)", low, high)
		}
	})

	t.Run("1号の場合は下限クランプ", func(t *testing.T) {
		// Arrange
		rs, _ := NewRingSize(41.0) // 1号

		// Act
		low, _ := rs.JPSizeRange()

		// Assert
		if low != 1 {
			t.Errorf("JPSizeRange() low = %d, want 1", low)
		}
	})

	t.Run("25号の場合は上限クランプ", func(t *testing.T) {
		// Arrange
		rs, _ := NewRingSize(66.0) // 25号

		// Act
		_, high := rs.JPSizeRange()

		// Assert
		if high != 25 {
			t.Errorf("JPSizeRange() high = %d, want 25", high)
		}
	})
}

func TestCircumferenceForJPSize(t *testing.T) {
	t.Run("号数から周囲長を逆引きできる", func(t *testing.T) {
		tests := []struct {
			name string
			size int
			want float64
		}{
			{"1号", 1, 41.0},
			{"10号", 10, 50.5},
			{"13号", 13, 53.5},
			{"25号", 25, 66.0},
		}
		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				// Act
				got, err := CircumferenceForJPSize(tt.size)

				// Assert
				if err != nil {
					t.Fatalf("unexpected error: %v", err)
				}
				if got != tt.want {
					t.Errorf("CircumferenceForJPSize(%d) = %f, want %f", tt.size, got, tt.want)
				}
			})
		}
	})

	t.Run("範囲外の号数はエラー", func(t *testing.T) {
		for _, size := range []int{0, -1, 26} {
			if _, err := CircumferenceForJPSize(size); err == nil {
				t.Errorf("expected error for size %d", size)
			}
		}
	})
}

func TestRingSize_USSize(t *testing.T) {
	t.Run("USサイズ5前後", func(t *testing.T) {
		// Arrange
		rs, _ := NewRingSize(49.3)

		// Act
		got := rs.USSize()

		// Assert
		if math.Abs(got-5.0) > 0.2 {
			t.Errorf("USSize() = %f, want ~5.0", got)
		}
	})
}

func TestRingSize_EUSize(t *testing.T) {
	t.Run("EUサイズは周囲長の四捨五入", func(t *testing.T) {
		// Arrange
		rs, _ := NewRingSize(49.3)

		// Act
		got := rs.EUSize()

		// Assert
		if got != 49 {
			t.Errorf("EUSize() = %d, want 49", got)
		}
	})
}
