library("randomForest")
library("raster")
library("rgdal")
library("grid")
library("gridExtra")
library('rpart')
library('rpart.plot')
library('tree')
library('rpart.utils')
library('corrplot')
library('rfUtilities')
library('foreach')
library('doSNOW')
library('Boruta')

set.seed(1234567890)

setwd('/disco4/mapbiomas')

IMAGES_DIR   <- 'data/images/'
TRAINING_DIR <- 'data/training/'
OUTPUT_DIR   <- 'data/output/'

YEARS <- c(2010)
PREFIX <- 'L5A'

WRS <- c('220075', '221075', '223076') #era pra ser 221075
WRS <- c('217066', '219075', '220073', '223077', '225072', '226069', '230069', '218065', '220069', '221065', '223080', '225075', '227062', '232058')

POINTS_REFERENCE <- '_canasat_2011_pnt_10000'
POINTS_REFERENCE <- "_ifac_2010_pnt_10000"

POINTS <- c(1000, 3000, 10000)

PERIODS <- c('ACP_WET1', 'ACP_WET2', 'ACP_DRY1', 'ACP_DRY2', 'ACP_DRY3', 'ACP_WET3', 'ACP_ALL')
PERIODS <- c('ANNUAL')
VARIABLES <- c('ACP_WET1_BLUE_qmo', 'ACP_WET1_GREEN_qmo', 'ACP_WET1_RED_qmo', 'ACP_WET1_NIR_qmo', 'ACP_WET1_SWIR1_qmo', 'ACP_WET1_SWIR2_qmo', 'ACP_WET1_TIR1_qmo', 'ACP_WET1_TIR2_qmo', 'ACP_WET1_NDWI_qmo', 'ACP_WET1_NDVI_qmo', 'ACP_WET1_CAI_qmo', 'ACP_WET2_BLUE_qmo', 'ACP_WET2_GREEN_qmo', 'ACP_WET2_RED_qmo', 'ACP_WET2_NIR_qmo', 'ACP_WET2_SWIR1_qmo', 'ACP_WET2_SWIR2_qmo', 'ACP_WET2_TIR1_qmo', 'ACP_WET2_TIR2_qmo', 'ACP_WET2_NDWI_qmo', 'ACP_WET2_NDVI_qmo', 'ACP_WET2_CAI_qmo', 'ACP_DRY1_BLUE_qmo', 'ACP_DRY1_GREEN_qmo', 'ACP_DRY1_RED_qmo', 'ACP_DRY1_NIR_qmo', 'ACP_DRY1_SWIR1_qmo', 'ACP_DRY1_SWIR2_qmo', 'ACP_DRY1_TIR1_qmo', 'ACP_DRY1_TIR2_qmo', 'ACP_DRY1_NDWI_qmo', 'ACP_DRY1_NDVI_qmo', 'ACP_DRY1_CAI_qmo', 'ACP_DRY2_BLUE_qmo', 'ACP_DRY2_GREEN_qmo', 'ACP_DRY2_RED_qmo', 'ACP_DRY2_NIR_qmo', 'ACP_DRY2_SWIR1_qmo', 'ACP_DRY2_SWIR2_qmo', 'ACP_DRY2_TIR1_qmo', 'ACP_DRY2_TIR2_qmo', 'ACP_DRY2_NDWI_qmo', 'ACP_DRY2_NDVI_qmo', 'ACP_DRY2_CAI_qmo', 'ACP_DRY3_BLUE_qmo', 'ACP_DRY3_GREEN_qmo', 'ACP_DRY3_RED_qmo', 'ACP_DRY3_NIR_qmo', 'ACP_DRY3_SWIR1_qmo', 'ACP_DRY3_SWIR2_qmo', 'ACP_DRY3_TIR1_qmo', 'ACP_DRY3_TIR2_qmo', 'ACP_DRY3_NDWI_qmo', 'ACP_DRY3_NDVI_qmo', 'ACP_DRY3_CAI_qmo', 'ACP_WET3_BLUE_qmo', 'ACP_WET3_GREEN_qmo', 'ACP_WET3_RED_qmo', 'ACP_WET3_NIR_qmo', 'ACP_WET3_SWIR1_qmo', 'ACP_WET3_SWIR2_qmo', 'ACP_WET3_TIR1_qmo', 'ACP_WET3_TIR2_qmo', 'ACP_WET3_NDWI_qmo', 'ACP_WET3_NDVI_qmo', 'ACP_WET3_CAI_qmo', 'ACP_ALL_BLUE_qmo_median', 'ACP_ALL_GREEN_qmo_median', 'ACP_ALL_RED_qmo_median', 'ACP_ALL_NIR_qmo_median', 'ACP_ALL_SWIR1_qmo_median', 'ACP_ALL_SWIR2_qmo_median', 'ACP_ALL_TIR1_qmo_median', 'ACP_ALL_TIR2_qmo_median', 'ACP_ALL_NDWI_qmo_median', 'ACP_ALL_NDVI_qmo_median', 'ACP_ALL_CAI_qmo_median')
IGNORE_VARIABLES <- c("ACP_DRY2_CAI_qmo", "ACP_DRY2_TIR1_qmo",  "ACP_DRY3_TIR1_qmo",  "ACP_WET1_BLUE_qmo",  "ACP_WET1_TIR1_qmo",  "ACP_WET2_BLUE_qmo",  "ACP_WET2_GREEN_qmo", "ACP_WET3_BLUE_qmo",  "ACP_WET3_CAI_qmo", "ACP_WET3_TIR1_qmo", "ACP_DRY1_TIR2_qmo", "ACP_DRY2_TIR2_qmo", "ACP_DRY3_TIR2_qmo", "ACP_WET1_TIR2_qmo", "ACP_WET2_TIR1_qmo", "ACP_WET2_TIR2_qmo", "ACP_WET3_TIR2_qmo"  )

VARIABLES <- c("B1","B2","B3","B4","B5","B6","B7","B8","B9","B10","B11","B12","B13","B14","B15","B16","B17","B18","B19","B20","B21","B22","B23","B24","B25","B26","B27","B28","B29","B30","B31","B32","B33","B34","B35","B36","B37","B38","B39","B40","B41","B42","B43","B44","B45","B46","B47","B48","B49","B50","B51","B52","B53","B54","B55","B56","B57","B58","B59","B60","B61","B62","B63","B64","B65","B66","B67","B68","B69","B70","B71","B72","B73","B74","B75","B76","B77","B78","B79","B80","B81","B82","B83","B84","B85","B86","B87","B88","B89","B90","B91","B92","B93","B94","B95","B96","B97","B98","B99","B100","B101","B102","B103","B104","B105","B106","B107","B108","B109","B110")

IGNORE_VARIABLES <- c()


mb.loadImages <- function(dir, card, periods, variables, ignore_variables){
  images = stack()
   
  band_names <- c()

  for (period in periods){
      band_names <- c(band_names, period)
      filename <- paste0(paste(paste0(dir, card), period, sep = '_'), '.tif')
      print(filename)
      image = brick(filename)
      images <- stack(images, image)
  }
  print(names(images))
  names(images) <- variables
  desired_bands <- variables[! variables %in% ignore_variables]
  return (images[[desired_bands]])
}

mb.loadTrainingByWRS <- function(wrs, dir, POINTS_REFERENCE, format='.shp'){
  filename <- paste0(dir, wrs, POINTS_REFERENCE, format)
  print(filename)
  training <- shapefile(filename)
  return(training)
}

mb.extract <- function(images, training, nsample=NULL){
  if(!is.null(nsample)){
    nsample <- round(runif(n = nsample, min = 1, max = nrow(training)))
    training <-  training[nsample,]
  }
  data <- raster::extract(images, training, df=TRUE)
  data$desc <- as.factor(training$class)
  return(data)
}

mb.calc.collinearVariables <- function(model_variables, n, p){
  #analise das bandas 'ruins' com problema de multcolinearidade
  mcollinear <- multi.collinear(model_variables, perm = TRUE, leave.out = TRUE, n = n, p = p, na.rm = TRUE)
  mcollinear_frame <- data.frame(mcollinear)
  mcollinear_frame <- mcollinear_frame[with(mcollinear_frame, order(-frequency)),]
  return(mcollinear_frame)
}

mb.calc.modelSel <- function(model_variables, response_variables){
  #analise das bandas boas... selecionadas para a modelagem
  selection = rf.modelSel(model_variables, response_variables, imp.scale = "mir", r = c(0.25, 0.5, 0.75), final.model = FALSE, seed = NULL, parsimony = NULL)
  selection$importance$vars <- rownames(selection$importance)
  selection$importance <- selection$importance[with(selection$importance, order(-imp)),]
  return(selection)
}

mb.calc.importanceFrequence <- function(rf, p=0.3, plot=FALSE){
  #análise das floresta de arvores q o ramdomforest criou para checar se as bandas mais importantes foram as mais selecionadas pelas arvores
  rf_impfreq <- rf.imp.freq(rf, p = p, plot = plot)
  rf_impfreq$importance <- data.frame(rf_impfreq$importance)
  rf_impfreq$importance <- rf_impfreq$importance[with(rf_impfreq$importance, order(-MeanDecreaseAccuracy)),]
  rf_impfreq$frequency <- rf_impfreq$frequency[with(rf_impfreq$frequency, order(-var.freq)),]
  return(rf_impfreq)
}

mb.calc.accuracy <- function(predicted, observed){
  accuracy <- accuracy(predicted, observed)
  return(accuracy)
}

mb.plot.randomForest <- function(rf, model_variables, response_variables){
  collinearVariables  <- mb.calc.collinearVariables(model_variables, 100, 0.05)
  modelSel            <- mb.calc.modelSel(model_variables, response_variables)
  importanceFrequence <- mb.calc.importanceFrequence(rf, p=0.3, plot = FALSE)
  accuracy            <- mb.calc.accuracy(rf$predicted, response_variables)
  writeLines("\n ************ RF Basic ****************** \n")
  print(rf)
  writeLines("\n ********** RF Importance and Frequence (importance(rf) ****************** \n")
  print(importanceFrequence)
  writeLines("\n ************ RF Collinear Variables ****************** \n")
  print(collinearVariables)
  writeLines("\n ************ RF Selection model ****************** \n")
  print(modelSel)
  writeLines("\n ************ RF Accuracy ****************** \n")
  print(accuracy)
  plot(modelSel, imp = "sel")
}

mb.plot.rpart <- function(rp){
  writeLines("\n ************ Rpart ****************** \n")
  print(rp)
  writeLines("\n ************ Rpart CP *************** \n")
  printcp(rp)
  rpart.plot(x=rp)
}

mb.plot.tree <- function(tree){
  writeLines("\n ************ Tree ******************* \n")
  print(tree)
  writeLines("\n **********Tree Summary ************** \n")
  print(summary(tree))
}

mb.plot.rasterStack <- function(rasterStack){
  for(layer in as.list(rasterStack)){
    color <- gray.colors(255, start = 0, end = 1, gamma = 2, alpha = NULL)
    plot(layer, xlab=toString(names(layer)), col = color)
  }
}

mb.plot.correlationMatrix <- function(cor_variables, method="ellipse", type="lower"){
  correlation <- corrplot(cor(cor_variables), method = method, type = type,tl.cex = 0.3, tl.col = "indianred4", order="hclust", sig.level = 0.01)
  return(correlation)
}

mb.processWRS <- function(w){
  for(y in YEARS){
    card_name<- paste(PREFIX, y, w, sep = '_') #L5_T1_TOA_200069_2007

    images <- mb.loadImages(IMAGES_DIR, card_name, PERIODS, VARIABLES, IGNORE_VARIABLES)
    print("Images carregadas!")
    print(names(images))
    training <- mb.loadTrainingByWRS(w, TRAINING_DIR, POINTS_REFERENCE)
    print("Treinamento carregado!")

    #pdf(paper="a4", file = paste0(OUTPUT_DIR, card_name,"_", "VARIABLES.pdf"))
    #mb.plot.rasterStack(images)
    #dev.off()

    for(p in POINTS){
      roi_data <- na.exclude(mb.extract(images, training, p))
      roi_data_tree <- na.exclude(mb.extract(images, training, 200))

      model_variables <- roi_data[,names(images)]
      response_variables <- roi_data$desc
      
      
      f <- eval( parse(text = paste('desc', paste(names(images), collapse=" + ") , sep=' ~ '))) # formula RandomForest
      print(f)
      print("Antes de iniciar o RF")
      roi_data.rf <- randomForest(f, data=roi_data, ntree=5000, importance=TRUE, proximity=TRUE, do.trace=T)
      roi_data.rp <- rpart(f, data=roi_data, method = 'class')
      roi_data.rpt <- tree(f, data=roi_data_tree, split = 'gini')
      roi_data.bor <- Boruta(f, data=roi_data, doTrace=2)
      print("Depois de calcular o RF")

      pdf(paper="a4", file = paste0(OUTPUT_DIR, card_name,"_", POINTS_REFERENCE, toString(p), ".pdf"))
      sink(file = paste0(OUTPUT_DIR, card_name,"_", POINTS_REFERENCE, toString(p), ".txt"))
	
      #plotRGB(stack(images$WET_qmo_NIR, images$WET_qmo_SWIR1, images$WET_qmo_RED), scale = 10000, zlim=c(0, 10000))
	
	
      tryCatch({
	mb.plot.randomForest(roi_data.rf, model_variables, response_variables)
      })
      tryCatch({
      	mb.plot.rpart(roi_data.rp)
      })
      tryCatch({
      	mb.plot.tree(roi_data.rpt)
      })
      
      writeLines("\n ************ Boruta ******************* \n")
      plot(roi_data.bor)
      print(roi_data.bor)
      print(cbind(names(roi_data.bor$finalDecision), as.character(roi_data.bor$finalDecision)))      

      #for (period in PERIODS){
      #  mb.plot.correlationMatrix(model_variables[,grep(pattern = period, names(images))])
      #}
      #for (band in BANDS[!BANDS %in% IGNORE_BANDS]){
      #  mb.plot.correlationMatrix(model_variables[,grep(pattern = band, names(images))])
      #}
      #for (reducer in REDUCERS){
      #  mb.plot.correlationMatrix(model_variables[,grep(pattern = reducer, names(images))])
      #}

      sink()
      dev.off()
    }
  }
}

cluster <- makeCluster(8, outfile = 'data/mapbiomas.log')
registerDoSNOW(cluster)

#for(wrs in WRS){
#	mb.processWRS(wrs)
#}

foreach (wrs=WRS, .packages = c("randomForest", "rgdal", "grid", "gridExtra", "rpart", "rpart.plot", "tree", "rpart.utils", "corrplot", "rfUtilities", "raster", "Boruta", "doSNOW") ) %dopar% {  
      mb.processWRS(wrs)
}

#save.image(file = 'environment.RData')
#load(file = 'environment.RData')

#plot(images$L5_T1_TOA_221065_2007_WET_min.10)

# Predict!

# image_class <- images
# names(image_class) <- bands
# image_pred <- predict(image_class, model=rf, na.rm=T)
#
# colors <- c(rgb(0, 150, 0, maxColorValue=255),  # Forest
#             rgb(0, 0, 255, maxColorValue=255),  # Water
#             rgb(0, 255, 0, maxColorValue=255),  # Herbaceous
#             rgb(160, 82, 45, maxColorValue=255),  # Barren
#             rgb(255, 0, 0, maxColorValue=255))  # Urban
#
# #plotRGB(image_pred, r=4, g=5, b=3, stretch="lin")ROOT_DIR
# plot(image_pred, col=colorRampPalette(c("red", "white", "blue"))(255))

# pdf:
# imagem
# rpart plot
# tree plot + text
# tree print  (capture.output())
# rf varImpPlot
# rf proximity

# txt
# nome da imagem
# nome dos pontos
# CART(rpart)
# rpart print
# rpart printcp
# CART(tree)
# tree print
# tree summary
# RANDOMFOREST
# rf print
# rf importance (ordenado)
