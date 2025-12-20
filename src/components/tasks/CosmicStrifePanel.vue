<template>
  <div class="cosmic-strife-panel">
    <div class="panel-section">
      <div class="section-header">
        <input
          type="checkbox"
          id="enable-cosmic-strife"
          v-model="modelValue.EnabledTasks[3]"
          class="section-checkbox"
        />
        <label for="enable-cosmic-strife" class="section-title">{{ t('tasks.cosmicStrife.title') }}</label>
      </div>

      <div class="section-content">
        <!-- 差分宇宙 -->
        <div class="subsection">
          <div class="subsection-header">
            <input
              type="checkbox"
              id="simulated-universe"
              v-model="modelValue.SimulatedUniverseEnable"
              class="subsection-checkbox"
            />
            <label for="simulated-universe" class="subsection-title">{{ t('tasks.cosmicStrife.proteanHero') }}</label>
          </div>

          <div class="subsection-content">
            <div class="form-group">
              <label class="form-label">{{ t('tasks.cosmicStrife.mode') }}</label>
              <CustomDropdown
                v-model="modelValue.SimulatedUniverseMode"
                :options="simulatedUniverseModeOptions"
                placeholder=""
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ t('tasks.cosmicStrife.runTimes') }}</label>
              <input
                v-model.number="modelValue.SimulatedUniverseRunTimes"
                type="number"
                min="1"
                max="99999"
                class="form-input"
              />
            </div>
          </div>

          <p class="hint-text">{{ t('tasks.cosmicStrife.hintText') }}</p>
        </div>

        <!-- 货币战争 -->
        <div class="subsection">
          <div class="subsection-header">
            <input
              type="checkbox"
              id="currency-wars"
              v-model="modelValue.CurrencyWarsEnable"
              class="subsection-checkbox"
            />
            <label for="currency-wars" class="subsection-title">{{ t('tasks.cosmicStrife.currencyWars') }} - {{ t('tasks.cosmicStrife.zeroSumGame') }}</label>
          </div>

          <div class="subsection-content">
            <div class="form-group">
              <label class="form-label">{{ t('tasks.cosmicStrife.trailblazer') }}</label>
              <input
                v-model="modelValue.CurrencyWarsUsername"
                type="text"
                class="form-input"
                placeholder=""
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ t('tasks.cosmicStrife.mode') }}</label>
              <CustomDropdown
                v-model="modelValue.CurrencyWarsMode"
                :options="currencyWarsModeOptions"
                placeholder=""
              />
            </div>

            <div class="form-group" v-if="isCwNormalMode">
              <label class="form-label">{{ t('tasks.cosmicStrife.difficulty') }}</label>
              <CustomDropdown
                v-model="modelValue.CurrencyWarsDifficulty"
                :options="currencyWarsDifficultyOptions"
                placeholder=""
              />
            </div>

            <div class="form-group" v-if="isCwNormalMode">
              <label class="form-label">{{ t('tasks.cosmicStrife.policy') }}</label>
              <CustomDropdown
                v-model="modelValue.CurrencyWarsPolicy"
                :options="currencyWarsPolicyOptions"
                placeholder=""
              />
            </div>

            <div class="form-group" v-if="isCwNormalMode">
              <label class="form-label">{{ t('tasks.cosmicStrife.runTimes') }}</label>
              <input
                v-model.number="modelValue.CurrencyWarsRunTimes"
                type="number"
                min="1"
                max="99999"
                class="form-input"
              />
            </div>

            <!-- 刷开局配置 -->
            <div v-if="!isCwNormalMode" class="reroll-config">
              <p class="hint-text">刷开局将默认使用最高难度。下方可配置需要的投资环境与投资策略（用空格分隔多个）。</p>
              
              <div class="form-group">
                <label class="form-label">投资环境</label>
                <input
                  v-model="modelValue.CwRsInvestEnvironments"
                  type="text"
                  class="form-input"
                  placeholder="例如：长线利好 轮岗"
                />
              </div>

              <div class="form-group">
                <label class="form-label">投资策略</label>
                <input
                  v-model="modelValue.CwRsInvestStrategies"
                  type="text"
                  class="form-input"
                  placeholder="例如：砂里淘金"
                />
              </div>

              <div class="form-group">
                <label class="form-label">策略阶段</label>
                <input
                  v-model.number="modelValue.CwRsInvestStrategyStage"
                  type="number"
                  min="1"
                  max="2"
                  class="form-input"
                />
              </div>

              <div class="form-group">
                <label class="form-label">最大尝试轮数</label>
                <input
                  v-model.number="modelValue.CwRsMaxRetry"
                  type="number"
                  min="0"
                  max="99999"
                  class="form-input"
                />
              </div>
            </div>
          </div>

          <p class="hint-text">{{ t('tasks.cosmicStrife.hintText') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import CustomDropdown from '../CustomDropdown.vue'
import { useTranslation } from '../../composables/useTranslation'

const { t } = useTranslation()

const props = defineProps<{
  modelValue: any
}>()

const isCwNormalMode = computed(() => props.modelValue.CurrencyWarsMode !== 2)

const simulatedUniverseModeOptions = computed(() => [
  { label: t('tasks.cosmicStrife.singleLayer').value, value: 0 }
])

const currencyWarsPolicyOptions = computed(() => [
  { label: t('tasks.cosmicStrife.standardGambit').value, value: 0 },
  { label: t('tasks.cosmicStrife.overclockGambit').value, value: 1 }
])

const currencyWarsModeOptions = computed(() => [
  { label: '标准博弈', value: 0 },
  { label: '超频博弈', value: 1 },
  { label: '刷开局', value: 2 }
])

const currencyWarsDifficultyOptions = computed(() => [
  { label: '最低难度', value: 0 },
  { label: '最高难度', value: 1 }
])
</script>

<style scoped>
.cosmic-strife-panel {
  /* 移除固定高度，让内容自然撑开 */
}

.panel-section {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  padding: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.section-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #007bff;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #000;
  cursor: pointer;
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-left: 26px;
}

.subsection {
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 12px;
}

.subsection-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.subsection-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #007bff;
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: #000;
  cursor: pointer;
}

.subsection-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 24px;
  margin-bottom: 8px;
}

.form-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-label {
  width: 100px;
  font-size: 14px;
  font-weight: 500;
  color: #000;
  flex-shrink: 0;
}

.form-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.form-input[type="number"] {
  -moz-appearance: textfield;
}

.form-input[type="number"]::-webkit-inner-spin-button,
.form-input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.hint-text {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.reroll-config {
  padding-left: 0;
  margin-top: 8px;
}

.reroll-config .hint-text {
  margin-bottom: 12px;
  padding: 8px;
  background: rgba(33, 150, 243, 0.1);
  border-left: 3px solid #2196f3;
  border-radius: 4px;
  font-style: normal;
}

@media (prefers-color-scheme: dark) {
  .panel-section {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .subsection {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .section-title,
  .subsection-title,
  .form-label {
    color: #fff;
  }

  .form-input {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
    color: #fff;
  }

  .hint-text {
    color: #ccc;
  }

  .reroll-config .hint-text {
    background: rgba(33, 150, 243, 0.2);
    color: #90caf9;
  }
}
</style>
