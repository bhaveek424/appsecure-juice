from enum import StrEnum


class ReviewSkillId(StrEnum):
    ACCOUNT_BOUNDARY = "account-boundary"
    BASKET_AND_CHECKOUT = "basket-and-checkout"
    REVIEW_OWNERSHIP = "review-ownership"
    COUPON_AND_DISCOUNT = "coupon-and-discount"


REVIEW_SKILL_NAMES: dict[ReviewSkillId, str] = {
    ReviewSkillId.ACCOUNT_BOUNDARY: "Account Boundary",
    ReviewSkillId.BASKET_AND_CHECKOUT: "Basket And Checkout",
    ReviewSkillId.REVIEW_OWNERSHIP: "Review Ownership",
    ReviewSkillId.COUPON_AND_DISCOUNT: "Coupon And Discount",
}
